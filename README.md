# inspectds

![GitHub release (latest by date)](https://img.shields.io/github/v/release/pmav99/inspectds)
![CI](https://github.com/pmav99/inspectds/actions/workflows/run_tests.yml/badge.svg)

A CLI utility to print metadata of datasets in various formats (e.g. NetCDF, zarr, GRIB etc)

*powered by xarray*

## Installation

```
pipx install 'git+https://github.com/pmav99/inspectds.git'

# or if you want support for GRIB

pipx install 'git+https://github.com/pmav99/inspectds.git#egg=inspectds[grib]'
```

## Usage

### Netcdf
```
$ inspectds netcdf tests/data/example_1.nc

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
$ inspectds zarr tests/data/store.zarr

Dimensions: (lat: 19, lon: 36, time: 12)
Coordinates:
  * lat      (lat) int64 -90 -80 -70 -60 -50 -40 -30 ... 30 40 50 60 70 80 90
  * lon      (lon) int64 -180 -170 -160 -150 -140 -130 ... 130 140 150 160 170
  * time     (time) datetime64[ns] 2001-01-31 2001-02-28 ... 2001-12-31
Data variables:
    aaa      (lon, lat, time) int64 ...
```

### More info:

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
set `LD_LIBRARY_PATH` before running `inspectds`. E.g.:

```
LD_LIBRARY_PATH="${CONDA_PREFIX}"/lib inspectds grib /path/to/example.grib

# or
export LD_LIBRARY_PATH="${CONDA_PREFIX}"/lib
inspectds grib /path/to/example.grib
```

will result in:

```
Dimensions: (isobaricInhPa: 2, latitude: 3, longitude: 4, number: 2, time: 3)
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
