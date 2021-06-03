# inspectds

A CLI utility to print metadata of datasets in various formats (e.g. NetCDF, zarr, etc)

*powered by xarray*

## Installation

```
pipx install 'git+https://github.com/pmav99/inspectds.git'

# or if you want support for GRIB

pipx install 'git+https://github.com/pmav99/inspectds.git#egg=inspectds[grib]'
```

## Usage

```
inspectds --help
inspectds grib --help   # requires extras
inspectds netcdf --help
inspectds zarr --help
```

## GRIB support

The GRIB format is supported but there are non-python dependencies which must be satisfied. More
specifically, `libeccodes.so` must be available. If you did **not** install `eccodes` with your
distro's package manager (e.g. you compiled from source or installed via `conda`) then you should
set `LD_LIBRARY_PATH` before running `inspectds`:

```
LD_LIBRARY_PATH="${CONDA_PREFIX}"/lib inspectds grib /path/to/example.grib

# or
export LD_LIBRARY_PATH="${CONDA_PREFIX}"/lib
inspectds grib /path/to/example.grib
```
