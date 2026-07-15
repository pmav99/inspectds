import pathlib

import numpy as np
import pytest
import xarray as xr
from typer.testing import CliRunner

from inspectds.cli import app
from inspectds.cli import DATASET_TYPE
from inspectds.cli import echo_dataset
from inspectds.cli import get_filename_or_obj
from inspectds.cli import infer_dataset_type
from inspectds.cli import is_icechunk_repo

runner = CliRunner()


def _create_materialized_archive(archive: pathlib.Path) -> None:
    import icechunk as ic

    repo = ic.Repository.create(ic.local_filesystem_storage(str(archive)))
    session = repo.writable_session("main")
    ds = xr.Dataset(
        data_vars={"temperature": (("time", "lat"), np.arange(6.0).reshape(3, 2))},
        coords={"time": [0, 1, 2], "lat": [10.0, 20.0]},
        attrs={"title": "materialized demo"},
    )
    ds.to_zarr(session.store, zarr_format=3, consolidated=False)
    session.commit("init")


def _create_virtual_archive(archive: pathlib.Path, source_root: pathlib.Path) -> None:
    import icechunk as ic
    from obspec_utils.registry import ObjectStoreRegistry
    from obstore.store import from_url
    from virtualizarr import open_virtual_dataset
    from virtualizarr.parsers import HDFParser

    source_root.mkdir(parents=True, exist_ok=True)
    prefix = f"file://{source_root}/"
    nc = source_root / "data.nc"
    ds = xr.Dataset(
        data_vars={"temp": (("time", "lat"), np.arange(6.0).reshape(3, 2))},
        coords={"time": [0, 1, 2], "lat": [10.0, 20.0]},
        attrs={"title": "virtual demo"},
    )
    ds.to_netcdf(nc, engine="netcdf4", format="NETCDF4")

    config = ic.RepositoryConfig.default()
    container = ic.VirtualChunkContainer(prefix, ic.local_filesystem_store(str(source_root)))
    config.set_virtual_chunk_container(container)
    # icechunk >=2 wants an explicit no-auth sentinel for local containers; 1.x takes None.
    sentinel = getattr(getattr(ic, "credentials", None), "LocalFileSystemAccess", None)
    repo = ic.Repository.create(
        ic.local_filesystem_storage(str(archive)),
        config=config,
        authorize_virtual_chunk_access={prefix: sentinel},
    )
    repo.save_config()

    registry = ObjectStoreRegistry({prefix: from_url(prefix)})
    vds = open_virtual_dataset(f"file://{nc}", registry=registry, parser=HDFParser())
    session = repo.writable_session("main")
    vds.vz.to_icechunk(session.store)
    session.commit("virtual data")


def test_materialized_icechunk_archive_is_inspected(tmp_path: pathlib.Path) -> None:
    icechunk = pytest.importorskip("icechunk")
    archive = tmp_path / "materialized"
    _create_materialized_archive(archive)

    assert is_icechunk_repo(archive)
    assert infer_dataset_type(archive) == DATASET_TYPE.ICECHUNK
    assert isinstance(get_filename_or_obj(archive, DATASET_TYPE.ICECHUNK), icechunk.IcechunkStore)

    result = runner.invoke(app, [archive.as_posix(), "--full"])
    assert result.exit_code == 0
    assert "Dimensions" in result.stdout
    assert "temperature" in result.stdout
    assert "10.0 20.0" in result.stdout  # coordinate values are loaded


def test_virtual_icechunk_archive_loads_coordinates(tmp_path: pathlib.Path) -> None:
    pytest.importorskip("icechunk")
    pytest.importorskip("virtualizarr")
    pytest.importorskip("h5py")
    pytest.importorskip("obstore")
    pytest.importorskip("obspec_utils")
    archive = tmp_path / "virtual"
    _create_virtual_archive(archive, tmp_path / "src")

    assert infer_dataset_type(archive) == DATASET_TYPE.ICECHUNK
    result = runner.invoke(app, [archive.as_posix()])
    assert result.exit_code == 0
    # The coordinate chunks live in the source netcdf; showing their values proves
    # the recorded file:// virtual-chunk container was authorized on open.
    assert "10.0 20.0" in result.stdout


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
