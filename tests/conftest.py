import numpy as np
import pandas as pd
import pytest
import xarray as xr


@pytest.fixture
def sample_dataset() -> xr.Dataset:
    # create a dataset
    lon = np.arange(-180, 180, 10)
    lat = np.arange(-90, 91, 10)
    timestamps = pd.date_range("2001-01-01", "2001-12-31", name="time", freq="M")
    ds = xr.Dataset(
        data_vars=dict(
            aaa=(
                ["lon", "lat", "time"],
                np.random.randint(0, 101, (len(lon), len(lat), len(timestamps))),
            )
        ),
        coords=dict(
            lon=lon,
            lat=lat,
            time=timestamps,
        ),
    )
    return ds
