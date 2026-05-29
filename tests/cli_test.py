import pathlib

import pytest
import xarray as xr
from typer.testing import CliRunner

from inspectds.cli import app
from inspectds.cli import DATASET_TYPE
from inspectds.cli import echo_dataset
from inspectds.cli import get_filename_or_obj

runner = CliRunner()


def assert_line_order(stdout: str, *needles: str) -> None:
    line_numbers = []
    lines = stdout.splitlines()
    for needle in needles:
        line_numbers.append(next(index for index, line in enumerate(lines) if needle in line))
    assert line_numbers == sorted(line_numbers)


@pytest.mark.parametrize(
    "path", [pytest.param(path, id=path.name) for path in pathlib.Path("tests/data/").glob("*")]
)
def test_cli(path: pathlib.Path) -> None:
    if path.suffix == ".grib":
        pytest.importorskip("cfgrib")
    if path.suffix == ".slf":
        pytest.importorskip("xarray_selafin")
    result = runner.invoke(app, [path.as_posix()])
    assert result.exit_code == 0
    assert "Dimensions" in result.stdout
    assert "attributes" not in result.stdout


@pytest.mark.parametrize(
    "path",
    [
        pathlib.Path("tests/data/store.zarr.zip"),
        pathlib.Path("tests/data/consolidated.zarr.zip"),
    ],
)
def test_zipped_zarr_paths_are_opened_with_zipstore(path: pathlib.Path) -> None:
    zarr = pytest.importorskip("zarr")

    filename_or_obj = get_filename_or_obj(
        path=path,
        dataset_type=DATASET_TYPE.ZARR,
    )
    assert isinstance(filename_or_obj, zarr.storage.ZipStore)


def test_data_variables_are_displayed_in_natural_sort_order(capsys: pytest.CaptureFixture[str]) -> None:
    ds = xr.Dataset(
        data_vars={
            "var10": ("x", [10]),
            "var2": ("x", [2]),
            "var1": ("x", [1]),
        },
        coords={"x": [0]},
    )

    echo_dataset(
        ds=ds,
        dimensions=False,
        coordinates=False,
        variables=True,
        variable_attributes=False,
        global_attributes=False,
    )

    stdout = capsys.readouterr().out
    assert_line_order(stdout, "var1 ", "var2 ", "var10 ")


def test_dimensions_are_displayed_in_natural_sort_order(capsys: pytest.CaptureFixture[str]) -> None:
    ds = xr.Dataset(coords={"dim10": [0], "dim2": [0], "dim1": [0]})

    echo_dataset(
        ds=ds,
        dimensions=True,
        coordinates=False,
        variables=False,
        variable_attributes=False,
        global_attributes=False,
    )

    stdout = capsys.readouterr().out
    assert stdout == "Dimensions: (dim1: 1, dim2: 1, dim10: 1)\n"


def test_coordinates_are_displayed_in_natural_sort_order(capsys: pytest.CaptureFixture[str]) -> None:
    ds = xr.Dataset(
        coords={
            "coord10": ("x", [10]),
            "coord2": ("x", [2]),
            "coord1": ("x", [1]),
            "x": [0],
        },
    )

    echo_dataset(
        ds=ds,
        dimensions=False,
        coordinates=True,
        variables=False,
        variable_attributes=False,
        global_attributes=False,
    )

    stdout = capsys.readouterr().out
    assert_line_order(stdout, "coord1 ", "coord2 ", "coord10 ")


def test_attributes_are_displayed_in_natural_sort_order(capsys: pytest.CaptureFixture[str]) -> None:
    ds = xr.Dataset(
        data_vars={
            "var10": ("x", [10]),
            "var2": ("x", [2]),
            "var1": ("x", [1]),
        },
        coords={"x": [0]},
        attrs={
            "global10": 10,
            "global2": 2,
            "global1": 1,
        },
    )
    ds["var1"].attrs.update(
        {
            "attr10": 10,
            "attr2": 2,
            "attr1": 1,
        }
    )

    echo_dataset(
        ds=ds,
        dimensions=False,
        coordinates=False,
        variables=False,
        variable_attributes=True,
        global_attributes=True,
    )

    stdout = capsys.readouterr().out
    assert_line_order(stdout, "var1(x)", "var2(x)", "var10(x)")
    assert_line_order(stdout, "var1:attr1 =", "var1:attr2 =", "var1:attr10 =")
    assert_line_order(stdout, ":global1 =", ":global2 =", ":global10 =")
