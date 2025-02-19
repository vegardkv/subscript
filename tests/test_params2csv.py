import os
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from subscript.params2csv import params2csv


def test_main(tmp_path, mocker):
    """Test invocation from command line"""
    os.chdir(tmp_path)
    Path("parameters1.txt").write_text(
        "\n".join(["FOO     100", "BAR com", "BOGUS", "CONSTANT 1"]), encoding="utf8"
    )

    Path("parameters2.txt").write_text(
        "\n".join(["FOO 200", "BAR dot", "CONSTANT 1", "ONLYIN2 2"]), encoding="utf8"
    )

    mocker.patch("sys.argv", ["params2csv", "parameters1.txt", "parameters2.txt"])
    params2csv.main()

    result = pd.read_csv("params.csv")
    assert "FOO" in result
    assert "BAR" in result
    assert "CONSTANT" not in result
    assert "BOGUS" not in result
    assert "filename" in result
    assert set(result["filename"].values) == set(["parameters1.txt", "parameters2.txt"])

    # Test the cleaning mode:
    mocker.patch(
        "sys.argv", ["params2csv", "--clean", "parameters1.txt", "parameters2.txt"]
    )
    params2csv.main()
    assert Path("parameters2.txt.backup").exists()
    assert Path("parameters1.txt.backup").exists()

    cleanedparams1 = Path("parameters1.txt").read_text(encoding="utf8").splitlines()
    cleanedparams2 = Path("parameters2.txt").read_text(encoding="utf8").splitlines()

    assert len(cleanedparams1) == len(cleanedparams2) == 5

    # Check that the ONLYIN2 parameter was passed on to parameters1.txt:
    assert any("ONLYIN2" in x for x in cleanedparams1)

    # Check that BOGUS was transferred to parameters2.txt:
    assert any("BOGUS" in x for x in cleanedparams2)

    # Check that we allow a file not to exist:
    mocker.patch(
        "sys.argv",
        ["params2csv", "parameters1.txt", "parametersFOO.txt", "parameters2.txt"],
    )
    params2csv.main()
    result = pd.read_csv("params.csv")
    assert "FOO" in result
    assert "BAR" in result
    assert "CONSTANT" not in result
    assert "BOGUS" not in result
    assert "filename" in result
    assert set(result["filename"].values) == set(["parameters1.txt", "parameters2.txt"])


def test_spaces_in_values(tmp_path, mocker):
    """Test that we support spaces in values in parameters.txt
    if they are quoted properly"""
    os.chdir(tmp_path)
    Path("parameters.txt").write_text('somekey "value with spaces"', encoding="utf8")
    # Single-qoutes:
    Path("parameters2.txt").write_text("somekey 'value with spaces'", encoding="utf8")

    mocker.patch("sys.argv", ["params2csv", "--keepconstantcolumns", "parameters.txt"])
    params2csv.main()
    result = pd.read_csv("params.csv")
    assert "somekey" in result
    assert result["somekey"].values[0] == "value with spaces"


def test_spaces_in_values_single_quotes(tmp_path, mocker):
    """Test that single quotes can also be used to support spaces in values"""
    os.chdir(tmp_path)
    Path("parameters.txt").write_text('somekey "value with spaces"', encoding="utf8")

    mocker.patch("sys.argv", ["params2csv", "--keepconstantcolumns", "parameters.txt"])
    params2csv.main()
    result = pd.read_csv("params.csv")
    assert "somekey" in result
    assert result["somekey"].values[0] == "value with spaces"


@pytest.mark.integration
def test_integration():
    """Test that the endpoint is installed"""
    assert subprocess.check_output(["params2csv", "-h"])
