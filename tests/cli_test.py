import pathlib

import pytest

from typer.testing import CliRunner

from inspectds.cli import app


runner = CliRunner()


@pytest.mark.parametrize("archive", pathlib.Path("tests/data/").glob("*nc*"))
def test_netcdf(archive: pathlib.Path) -> None:
    result = runner.invoke(app, ["netcdf", archive.as_posix()])
    assert result.exit_code == 0
    assert "Dimensions" in result.stdout
    assert "attributes" not in result.stdout


@pytest.mark.parametrize("archive", pathlib.Path("tests/data/").glob("*zarr*"))
def test_zarr(archive: pathlib.Path) -> None:
    result = runner.invoke(app, ["zarr", archive.as_posix()])
    assert result.exit_code == 0
    assert "Dimensions" in result.stdout
    assert "attributes" not in result.stdout
