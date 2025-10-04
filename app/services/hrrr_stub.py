from __future__ import annotations
import numpy as np
import xarray as xr
from datetime import datetime, timedelta, timezone
from services.storage import get_zarr_target


async def ingest_hrrr_stub() -> int:
    # Create small synthetic grid representing HRRR variables
    time = np.array([np.datetime64(datetime.now(timezone.utc))])
    lat = np.linspace(25, 50, 50)
    lon = np.linspace(-125, -66, 60)
    LON, LAT = np.meshgrid(lon, lat)
    T2M = 280 + 5 * np.random.randn(len(lat), len(lon))
    U10M = np.random.randn(len(lat), len(lon))
    V10M = np.random.randn(len(lat), len(lon))
    ds = xr.Dataset(
        {
            "T2M": (("lat", "lon"), T2M),
            "U10M": (("lat", "lon"), U10M),
            "V10M": (("lat", "lon"), V10M),
        },
        coords={
            "time": time,
            "lat": lat,
            "lon": lon,
        },
    )
    target = get_zarr_target("hrrr_latest", partitioned=False)
    ds.to_zarr(target, mode="w")
    return int(T2M.size)
