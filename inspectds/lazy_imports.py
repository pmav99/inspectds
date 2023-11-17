from __future__ import annotations

import functools
import importlib
import types


@functools.cache
def import_xarray() -> types.ModuleType:
    xarray = importlib.import_module("xarray")
    return xarray
