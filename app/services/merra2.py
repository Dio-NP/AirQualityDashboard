from __future__ import annotations
from typing import Optional, List
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


def _search_merra2(product: Optional[str], time_range: Optional[str]):
    query = {
        "short_name": product or "M2T1NXSLV",
    }
    if time_range:
        query["temporal"] = time_range
    return earthaccess.search_data(**query)


def _download_first(results) -> List[str]:
    if not results:
        return []
    return earthaccess.download(results[:1], quiet=True)


def _nc_to_zarr(nc_path: str, zarr_name: str) -> int:
    ds = xr.open_dataset(nc_path, engine="netcdf4")
    # Select common surface variables if available
    wanted = [
        "T2M",   # 2-meter air temperature
        "U10M",  # 10-meter U wind
        "V10M",  # 10-meter V wind
        "QV2M",  # specific humidity 2m
        "PS",    # surface pressure
        "PRECTOT", # precipitation total
        "PBLH",  # planetary boundary layer height
    ]
    vars_avail = [v for v in wanted if v in ds]
    if not vars_avail:
        if len(ds.data_vars) == 0:
            return 0
        vars_avail = [list(ds.data_vars.keys())[0]]
    slim = ds[vars_avail]
    target = get_zarr_target(zarr_name, partitioned=False)
    slim.to_zarr(target, mode="w")
    return int(slim[vars_avail[0]].size)


async def ingest_merra2(product: Optional[str] = None, time_range: Optional[str] = None) -> int:
    _ensure_login()
    results = _search_merra2(product, time_range)
    files = _download_first(results)
    if not files:
        return 0
    count = 0
    for f in files:
        count += _nc_to_zarr(f, "merra2_latest")
    return count
