from fastapi import APIRouter, Query
from typing import List, Dict
import xarray as xr
import numpy as np
from services.storage import get_zarr_target
from services.cache import cache_get, cache_set
from services.aqi import categorize_aqi

router = APIRouter()


def _extract_points(ds: xr.Dataset, source: str, take: int) -> List[Dict]:
    out: List[Dict] = []
    if 'obs' not in ds.dims:
        return out
    n = int(ds.dims['obs'])
    idx = np.arange(max(0, n - take), n)
    lat = ds['lat'].values[idx]
    lon = ds['lon'].values[idx]
    val = ds['value'].values[idx]
    par = ds['parameter'].values[idx] if 'parameter' in ds else np.array(['unknown'] * len(idx))
    t = ds['time'].values[idx] if 'time' in ds else np.array([None] * len(idx))
    for i in range(len(idx)):
        try:
            value = float(val[i]) if np.isfinite(val[i]) else None
            out.append({
                'lat': float(lat[i]),
                'lon': float(lon[i]),
                'value': value,
                'aqi_category': categorize_aqi(value) if value is not None else None,
                'parameter': str(par[i]),
                'time': str(t[i]) if t is not None else None,
                'source': source,
            })
        except Exception:
            continue
    return out


@router.get('/stations')
def stations(limit: int = Query(default=200, ge=1, le=2000), page: int = Query(default=1, ge=1)) -> Dict[str, List[Dict]]:
    cache_key = f"stations:{limit}:{page}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached
    points: List[Dict] = []
    per_source = (limit // 2)
    for name, source in [("openaq_latest", "openaq"), ("airnow_latest", "airnow")]:
        try:
            path = get_zarr_target(name)
            ds = xr.open_zarr(path)
            # simple pagination over tail: increase window by page
            take = per_source * page
            points.extend(_extract_points(ds, source, take))
        except Exception:
            continue
    # Keep only the last "limit" points overall
    points = points[-limit:]
    result = {"points": points}
    cache_set(cache_key, result, ttl_seconds=60)
    return result
