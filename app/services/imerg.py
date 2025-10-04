from __future__ import annotations
from typing import Optional, List
import xarray as xr
import numpy as np

try:
    import earthaccess
except Exception:  # pragma: no cover
    earthaccess = None

from config import settings
from services.storage import get_zarr_target


def _ensure_login() -> None:
    if earthaccess is None:
        raise ImportError("earthaccess not installed")
    earthaccess.login(strategy="netrc", persist=True)


def _search_imerg(product: Optional[str], time_range: Optional[str]):
    # Defaults to Near Real-Time half-hourly Early product
    query = {
        "short_name": product or "GPM_3IMERGHH_E",
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
    # Try common IMERG precipitation variable names
    candidates = [
        "precipitationCal",  # final/gauge-corrected precipitation (mm/hr)
        "precipitation",     # generic precipitation field (mm/hr)
    ]
    var_name = None
    for v in candidates:
        if v in ds:
            var_name = v
            break
    if var_name is None:
        # Fallback: take first data var
        if len(ds.data_vars) == 0:
            return 0
        var_name = list(ds.data_vars.keys())[0]
    slim = ds[[var_name]]
    # Normalize variable name to 'precip' and keep coordinates
    slim = slim.rename({var_name: "precip"})
    target = get_zarr_target(zarr_name, partitioned=False)
    slim.to_zarr(target, mode="w")
    return int(slim["precip"].size)


async def ingest_imerg(product: Optional[str] = None, time_range: Optional[str] = None) -> int:
    _ensure_login()
    results = _search_imerg(product, time_range)
    files = _download_first(results)
    if not files:
        return 0
    count = 0
    for f in files:
        count += _nc_to_zarr(f, "imerg_latest")
    return count


