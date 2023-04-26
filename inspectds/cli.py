from __future__ import annotations

import enum
import pathlib
import typing
import warnings

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

    class DATASET_TYPE(enum.Enum):
        AUTO = "auto"
        GRIB = "grib"
        NETCDF = "netcdf"
        ZARR = "zarr"

else:
    SUPPORTED_DATASETS = {
        "netcdf",
        "zarr",
    }

    class DATASET_TYPE(enum.Enum):  # type: ignore[no-redef]
        AUTO = "auto"
        NETCDF = "netcdf"
        ZARR = "zarr"


app = typer.Typer(add_completion=False, invoke_without_command=True, add_help_option=True)


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
def infer_dataset_type(path: pathlib.Path) -> DATASET_TYPE:
    if path.suffix in (".grib", ".grib2"):
        dataset_type = DATASET_TYPE.GRIB
    elif path.is_dir() or path.suffix == ".zarr" or path.suffix == ".zip":
        dataset_type = DATASET_TYPE.ZARR
    else:
        dataset_type = DATASET_TYPE.NETCDF
    return dataset_type


@app.command(help=f"Print a dataset's metadata. Supports: {SUPPORTED_DATASETS}", no_args_is_help=True)
def inspect_dataset(
    path: pathlib.Path = typer.Argument(
        ...,
        dir_okay=True,
        file_okay=True,
        exists=True,
        readable=True,
        help="The path to the dataset",
    ),
    # fmt: off
    dataset_type: DATASET_TYPE = typer.Option(DATASET_TYPE.AUTO.value, help="The dataset type. If 'auto', then it gets inferred from PATH"),
    mask_and_scale: bool = typer.Option(False, help="Whether to mask and scale the dataset"),
    dimensions: bool = typer.Option(True, help="Whether to include 'Dimensions' in the output"),
    coordinates: bool = typer.Option(True, help="Whether to include 'Coordinates' in the output"),
    variables: bool = typer.Option(True, help="Whether to include 'Variables' in the output"),
    variable_attributes: bool = typer.Option(False, help="Whether to include the variable attributes in the output"),
    global_attributes: bool = typer.Option( False, help="Whether to include the global attributes in the output"),
    full: bool = typer.Option(False, help="Display full output. Overrides any other option"),
    # fmt: on
) -> int:
    if dataset_type is DATASET_TYPE.AUTO:
        dataset_type = infer_dataset_type(path)

    open_dataset_kwargs: dict[str, typing.Any] = {}
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
                raise typer.Exit()
        else:
            break

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
