# inspectds

![GitHub release (latest by date)](https://img.shields.io/github/v/release/pmav99/inspectds)
![CI](https://github.com/pmav99/inspectds/actions/workflows/run_tests.yml/badge.svg)

A CLI utility to print metadata of datasets in various formats (e.g. NetCDF, zarr, GRIB, tiff etc)

_powered by [xarray](https://github.com/pydata/xarray)_

## Prerequisites

You need the following binary dependencies:

- Python >= 3.9
- Optionally, [eccodes](https://github.com/ecmwf/eccodes), which is necessary for GRIB support.

## Installation

### conda

```
conda install -c conda-forge inspectds
```

### PyPI

The recommended way of installation is [pipx](https://github.com/pypa/pipx):

```
pipx install inspectds
```

or if you want support for GRIB, SELAFIN or both:

```
pipx install 'inspectds[grib]'
pipx install 'inspectds[selafin]'
pipx install 'inspectds[all]'
```

If you want to install the latest development version from git, then use:

```
pipx install 'git+https://github.com/pmav99/inspectds.git#egg=inspectds[all]'
```

Note: Support for GRIB also requires [eccodes](https://github.com/ecmwf/eccodes).
This is not a python dependency!
You need to install it via e.g. `apt` or `conda` or compile it from source or whatever.

## Usage

### Netcdf

```
$ inspectds tests/data/example_1.nc

Dimensions: (lat: 5, level: 4, lon: 10, time: 1)
Coordinates:
  * lat      (lat) int32 20 30 40 50 60
  * lon      (lon) int32 -160 -140 -118 -96 -84 -52 -45 -35 -25 -15
  * level    (level) int32 1000 850 700 500
  * time     (time) datetime64[ns] 1996-01-01T12:00:00
Data variables:
    temp     (time, level, lat, lon) float32 ...
    rh       (time, lat, lon) float32 ...
```

### Zarr

```
$ inspectds tests/data/store.zarr

Dimensions: (lat: 19, lon: 36, time: 12)
Coordinates:
  * lat      (lat) int64 -90 -80 -70 -60 -50 -40 -30 ... 30 40 50 60 70 80 90
  * lon      (lon) int64 -180 -170 -160 -150 -140 -130 ... 130 140 150 160 170
  * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-12-31
Data variables:
    aaa      (lon, lat, time) int64 ...
```

### Tiff

```
$ inspectds ETOPO_2022_v1_60s_N90W180_surface.tif
Dimensions: (band: 1, x: 21600, y: 10800)
Coordinates:
  * band         (band) int64 8B 1
  * x            (x) float64 173kB -180.0 -180.0 -180.0 ... 180.0 180.0 180.0
  * y            (y) float64 86kB 89.99 89.97 89.96 ... -89.96 -89.98 -89.99
    spatial_ref  int64 8B 0
Data variables:
    band_data  (band, y, x) float32 933MB ...
```

### GRIB

```
$ inspectds tests/data/example.grib

Dimensions: (number: 2, time: 3, isobaricInhPa: 2, latitude: 3, longitude: 4)
Coordinates:
  * number         (number) int64 0 1
  * time           (time) datetime64[ns] 2017-01-01 ... 2017-01-02
    step           timedelta64[ns] ...
  * isobaricInhPa  (isobaricInhPa) float64 850.0 500.0
  * latitude       (latitude) float64 90.0 0.0 -90.0
  * longitude      (longitude) float64 0.0 90.0 180.0 270.0
    valid_time     (time) datetime64[ns] ...
Data variables:
    z        (number, time, isobaricInhPa, latitude, longitude) float32 ...
    t        (number, time, isobaricInhPa, latitude, longitude) float32 ...
```

### SELAFIN

```
$ inspectds tests/data/iceland.slf
Dimensions: (time: 13, node: 3526)
Coordinates:
    x        (node) float32 14kB -13.99 -14.97 -15.89 ... -13.52 -16.31 -12.28
    y        (node) float32 14kB 57.38 60.19 69.79 63.11 ... 66.37 69.34 63.52
  * time     (time) datetime64[ns] 104B 2017-10-01 ... 2017-10-01T12:00:00
Data variables:
    S        (time, node) float32 183kB ...
```

### More info:

```
$ inspectds --help

 Usage: inspectds [OPTIONS] PATH

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    path      PATH  The path to the dataset [default: None] [required]                                                                                                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --dataset-type                                       [auto|netcdf|zarr|grib|selafin]  The dataset type. If 'auto', then it gets inferred from PATH [default: auto]                                                                                          │
│ --mask-and-scale         --no-mask-and-scale                                          Whether to mask and scale the dataset [default: no-mask-and-scale]                                                                                                    │
│ --dimensions             --no-dimensions                                              Whether to include 'Dimensions' in the output [default: dimensions]                                                                                                   │
│ --coordinates            --no-coordinates                                             Whether to include 'Coordinates' in the output [default: coordinates]                                                                                                 │
│ --variables              --no-variables                                               Whether to include 'Variables' in the output [default: variables]                                                                                                     │
│ --variable-attributes    --no-variable-attributes                                     Whether to include the variable attributes in the output [default: no-variable-attributes]                                                                            │
│ --global-attributes      --no-global-attributes                                       Whether to include the global attributes in the output [default: no-global-attributes]                                                                                │
│ --full                   --no-full                                                    Display full output. Overrides any other option [default: no-full]                                                                                                    │
│ --version                                                                             Display the version                                                                                                                                                   │
│ --help                                                                                Show this message and exit.                                                                                                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Development

```
mamba env create --file ci/py3.11.yml --name inspectds_dev
conda activate inspectds_dev
make init
make test
```
