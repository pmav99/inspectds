# pylint: disable=too-many-arguments
import pathlib

import typer
import xarray as xr

try:
    import cfgrib  # type: ignore  # pylint: disable=unused-import  # noqa

    IS_GRIB_AVAILABLE = True
except ImportError:
    IS_GRIB_AVAILABLE = False
except RuntimeError:
    IS_GRIB_AVAILABLE = False

app = typer.Typer(add_completion=False, invoke_without_command=False, add_help_option=True)


def echo_variable_attributes(ds: xr.Dataset) -> None:
    lines = []
    lines.append("Variable Attributes:")
    for name, da in ds.variables.items():
        dims = ", ".join(da.dims)
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


if IS_GRIB_AVAILABLE:

    @app.command(help="Show GRIB archive info", no_args_is_help=True)
    def grib(
        path: pathlib.Path = typer.Argument(
            ...,
            dir_okay=False,
            file_okay=True,
            exists=True,
            readable=True,
            help="The path to the GRIB archive",
        ),
        mask_and_scale: bool = typer.Option(False, help="Whether to mask and scale the dataset"),
        dimensions: bool = typer.Option(True, help="Whether to include 'Dimensions' in the output"),
        coordinates: bool = typer.Option(True, help="Whether to include 'Coordinates' in the output"),
        variables: bool = typer.Option(True, help="Whether to include 'Variables' in the output"),
        variable_attributes: bool = typer.Option(
            False, help="Whether to include the variable attributes in the output"
        ),
        global_attributes: bool = typer.Option(
            False, help="Whether to include the global attributes in the output"
        ),
        full: bool = typer.Option(False, help="Display full output. Overrides any other option"),
    ) -> int:
        try:
            ds = xr.open_dataset(
                filename_or_obj=path,
                mask_and_scale=mask_and_scale,
                engine="cfgrib",
                backend_kwargs={"indexpath": ""},
            )
        except Exception as exc:
            typer.echo(f"Couldn't open the zarr archive: {str(exc)}")
            raise typer.Exit()
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


@app.command(help="Show NetCDF archive info", no_args_is_help=True)
def netcdf(
    path: pathlib.Path = typer.Argument(
        ...,
        dir_okay=False,
        file_okay=True,
        exists=True,
        readable=True,
        help="The path to the netcdf archive",
    ),
    mask_and_scale: bool = typer.Option(False, help="Whether to mask and scale the dataset"),
    dimensions: bool = typer.Option(True, help="Whether to include 'Dimensions' in the output"),
    coordinates: bool = typer.Option(True, help="Whether to include 'Coordinates' in the output"),
    variables: bool = typer.Option(True, help="Whether to include 'Variables' in the output"),
    variable_attributes: bool = typer.Option(
        False, help="Whether to include the variable attributes in the output"
    ),
    global_attributes: bool = typer.Option(
        False, help="Whether to include the global attributes in the output"
    ),
    full: bool = typer.Option(False, help="Display full output. Overrides any other option"),
) -> int:
    try:
        ds = xr.open_dataset(filename_or_obj=path, mask_and_scale=mask_and_scale)
    except Exception as exc:
        typer.echo(f"Couldn't open the zarr archive: {str(exc)}")
        raise typer.Exit()
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


@app.command(help="Show zarr archive info", no_args_is_help=True)
def zarr(
    path: pathlib.Path = typer.Argument(
        ..., dir_okay=True, file_okay=True, exists=True, readable=True, help="The path to the zarr archive"
    ),
    mask_and_scale: bool = typer.Option(False, help="Whether to mask and scale the dataset"),
    consolidated: bool = typer.Option(False, help="whether to treat the archive as consolidated"),
    dimensions: bool = typer.Option(True, help="Whether to include 'Dimensions' in the output"),
    coordinates: bool = typer.Option(True, help="Whether to include 'Coordinates' in the output"),
    variables: bool = typer.Option(True, help="Whether to include 'Variables' in the output"),
    variable_attributes: bool = typer.Option(
        False, help="Whether to include the variable attributes in the output"
    ),
    global_attributes: bool = typer.Option(
        False, help="Whether to include the global attributes in the output"
    ),
    full: bool = typer.Option(False, help="Display full output. Overrides any other option"),
) -> int:
    try:
        ds = xr.open_zarr(store=path, mask_and_scale=mask_and_scale, consolidated=consolidated)
    except Exception as exc:
        typer.echo(f"Couldn't open the zarr archive: {str(exc)}")
        raise typer.Exit()
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
