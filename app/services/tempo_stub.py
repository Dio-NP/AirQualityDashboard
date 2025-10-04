from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import os
import tempfile
import numpy as np
import xarray as xr

try:
    import earthaccess
except Exception:  # pragma: no cover
    earthaccess = None

from config import settings
from services.storage import get_zarr_target


def _ensure_login():
    if earthaccess is None:
        raise ImportError("earthaccess not installed")
    earthaccess.login(strategy="netrc", persist=True)


def _resolve_short_name(product: Optional[str], nrt: bool) -> str:
    # Map friendly aliases to TEMPO short_names
    if product:
        return product
    # Default to NO2 as a commonly used pollutant
    return "TEMPO_NO2_L3" if not nrt else "TEMPO_NO2_L2_NRT"


def _search_tempo(product: Optional[str], time_range: Optional[str], version: Optional[str], nrt: bool = False):
    short_name = _resolve_short_name(product, nrt)
    query = {
        "short_name": short_name,
    }
    if time_range:
        query["temporal"] = time_range
    if version:
        query["version"] = version
    return earthaccess.search_data(**query)


def _download_first(results) -> List[str]:
    if not results:
        return []
    return earthaccess.download(results[:1], quiet=True)


def _nc_to_zarr(nc_path: str, zarr_name: str) -> int:
    ds = xr.open_dataset(nc_path, engine="netcdf4")
    # Best-effort selection of variables; fall back to first data var
    candidates = [v for v in ["no2", "NO2", "hcho", "o3", "aerosol_index"] if v in ds]
    if not candidates:
        if len(ds.data_vars) == 0:
            return 0
        candidates = [list(ds.data_vars.keys())[0]]
    slim = ds[candidates]
    target = get_zarr_target(zarr_name, partitioned=False)
    slim.to_zarr(target, mode="w")
    return int(slim[candidates[0]].size)


async def ingest_tempo_stub(product: Optional[str] = None, time_range: Optional[str] = None, version: Optional[str] = None, nrt: bool = False) -> int:
    _ensure_login()
    # Default version based on product type
    if version is None:
        version = settings.tempo_version_nrt if nrt else settings.tempo_version_standard
    results = _search_tempo(product, time_range, version=version, nrt=nrt)
    files = _download_first(results)
    if not files:
        return 0
    count = 0
    for f in files:
        count += _nc_to_zarr(f, "tempo_latest")
    return count
