import enum
import warnings
from importlib.metadata import version
from pathlib import Path
from typing import Annotated
from typing import Any

import typer
import xarray as xr

try:
    import cfgrib as cfgrib

    IS_GRIB_AVAILABLE = True
except ImportError:
    IS_GRIB_AVAILABLE = False
except RuntimeError:
    IS_GRIB_AVAILABLE = False

if IS_GRIB_AVAILABLE:
    SUPPORTED_DATASETS = {
        "grib",
        "netcdf",
        "zarr",
    }

    class DATASET_TYPE(str, enum.Enum):
        AUTO = "auto"
        GRIB = "grib"
        NETCDF = "netcdf"
        ZARR = "zarr"

else:
    SUPPORTED_DATASETS = {
        "netcdf",
        "zarr",
    }

    class DATASET_TYPE(str, enum.Enum):  # type: ignore[no-redef]
        AUTO = "auto"
        NETCDF = "netcdf"
        ZARR = "zarr"


def echo_variable_attributes(ds: xr.Dataset) -> None:
    lines = []
    lines.append("Variable Attributes:")
    for name, da in ds.variables.items():
        dims = ", ".join(da.dims)  # type: ignore[arg-type]
        lines.append(f"\t{da.dtype} {name}({dims})")
        for key, value in da.attrs.items():
            lines.append(f"\t\t{name}:{key} = {value}")
    typer.echo("\n".join(lines))


def echo_global_attributes(ds: xr.Dataset) -> None:
    lines = []
    lines.append("Global attributes:")
    for key, value in ds.attrs.items():
        lines.append(f"\t:{key} = {value}")
    typer.echo("\n".join(lines))


def echo_dataset(
    ds: xr.Dataset,
    dimensions: bool,
    coordinates: bool,
    variables: bool,
    variable_attributes: bool,
    global_attributes: bool,
) -> None:
    if dimensions:
        dimensions_text = ", ".join(f"{key}: {value}" for (key, value) in ds.sizes.items())
        typer.echo(f"Dimensions: ({dimensions_text})")
    if coordinates:
        typer.echo(ds.coords)
    if variables:
        typer.echo(ds.data_vars)
    if variable_attributes:
        echo_variable_attributes(ds)
    if global_attributes:
        echo_global_attributes(ds)


# Xarray can infer the datatype on its own.
# Nevertheless:
# 1. it raises RunTime warnings
# 2. we want to pass extra arguments to `xr.open_dataset()`
# 3. we want to allow the user to override the inferring
# This is why we keep this function
def infer_dataset_type(path: Path) -> DATASET_TYPE:
    if path.suffix in (".grib", ".grib2"):
        if IS_GRIB_AVAILABLE:
            dataset_type = DATASET_TYPE.GRIB
        else:
            msg = "GRIB file detected, but GRIB support is not available. Please install cfgrib."
            typer.echo(msg)
            raise typer.Exit(code=1)
    elif path.is_dir() or path.suffix == ".zarr" or path.suffix == ".zip":
        dataset_type = DATASET_TYPE.ZARR
    else:
        dataset_type = DATASET_TYPE.NETCDF
    return dataset_type


def get_kwargs(dataset_type: DATASET_TYPE) -> dict[str, Any]:
    open_dataset_kwargs: dict[str, Any] = {}
    if IS_GRIB_AVAILABLE and dataset_type == DATASET_TYPE.GRIB:
        open_dataset_kwargs.update(
            dict(
                engine="cfgrib",
                backend_kwargs={"indexpath": ""},
            )
        )
    elif dataset_type == DATASET_TYPE.ZARR:
        open_dataset_kwargs.update(
            dict(
                engine="zarr",
                consolidated=False,
            )
        )
    elif dataset_type == DATASET_TYPE.NETCDF:
        open_dataset_kwargs.update(
            dict(
                engine="netcdf4",
            )
        )
    else:
        raise ValueError("WTF??? Unknown Dataset type...")
    return open_dataset_kwargs


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"inspectds version: {version('inspectds')}")
        raise typer.Exit(code=0)


app = typer.Typer(
    add_completion=False,
    add_help_option=True,
    help=f"Print a dataset's metadata. Supports: {SUPPORTED_DATASETS}",
)


@app.command(no_args_is_help=True)
def inspect_dataset(
    # fmt: off
    path: Annotated[Path, typer.Argument(dir_okay=True, file_okay=True, exists=True, readable=True, help="The path to the dataset")],
    dataset_type: Annotated[DATASET_TYPE, typer.Option(help="The dataset type. If 'auto', then it gets inferred from PATH")] = DATASET_TYPE.AUTO,
    mask_and_scale: Annotated[bool, typer.Option(help="Whether to mask and scale the dataset")] = False,
    dimensions: Annotated[bool, typer.Option(help="Whether to include 'Dimensions' in the output")] = True,
    coordinates: Annotated[bool, typer.Option(help="Whether to include 'Coordinates' in the output")] = True,
    variables: Annotated[bool, typer.Option(help="Whether to include 'Variables' in the output")] = True,
    variable_attributes: Annotated[bool, typer.Option(help="Whether to include the variable attributes in the output")] = False,
    global_attributes: Annotated[bool, typer.Option(help="Whether to include the global attributes in the output")] =False,
    full: Annotated[bool, typer.Option(help="Display full output. Overrides any other option")] = False,
    version: Annotated[bool, typer.Option("--version", help="Display the version", callback=version_callback, is_eager=True)] = False,
    # fmt: on
) -> int:
    if dataset_type == DATASET_TYPE.AUTO:
        dataset_type = infer_dataset_type(path)

    open_dataset_kwargs = get_kwargs(dataset_type=dataset_type)

    # Some netcdf files are not compatible with Xarray
    # More specifically you can't have a dimension as a variable too.
    # https://github.com/pydata/xarray/issues/1709#issuecomment-343714896
    # When we find such variables we drop them:
    drop_variables: list[str] = []
    while True:
        try:
            ds = xr.open_dataset(
                filename_or_obj=path,
                mask_and_scale=mask_and_scale,
                drop_variables=drop_variables,
                **open_dataset_kwargs,
            )
        except Exception as exc:
            if "already exists as a scalar variable" in str(exc):
                to_be_dropped = str(exc).split("'")[-2]
                drop_variables.append(to_be_dropped)
                warnings.warn(f"Dropping scalar variable: {to_be_dropped}", RuntimeWarning)
            else:
                typer.echo(f"Couldn't open {dataset_type.value} dataset: {str(exc)}")
                raise typer.Exit(code=33)
        else:
            break

    # Make sure that all the coordinates are loaded
    for coord in ds.coords:
        ds[coord].load()

    if full:
        dimensions = coordinates = variables = variable_attributes = global_attributes = True

    echo_dataset(
        ds=ds,
        dimensions=dimensions,
        coordinates=coordinates,
        variables=variables,
        variable_attributes=variable_attributes,
        global_attributes=global_attributes,
    )
    return 0
