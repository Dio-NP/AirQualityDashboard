from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np
import xarray as xr
from datetime import timezone

from services.storage import get_zarr_target


async def ingest_pandora_csv(url: str, parameter: Optional[str] = None) -> int:
    """
    Ingest a Pandora CSV export to Zarr. Expects columns including time and value; attempts
    to detect latitude/longitude if present. Parameter name can be provided to tag the dataset.
    """
    df = pd.read_csv(url)
    # Normalize time column
    time_col = None
    for c in df.columns:
        lc = str(c).lower()
        if lc in {"time", "datetime", "timestamp", "utc"}:
            time_col = c
            break
    if time_col is None:
        # Try combine date/time columns
        candidate_cols = [c for c in df.columns if str(c).lower() in {"date", "time_utc"}]
        if len(candidate_cols) >= 2:
            df["__dt"] = pd.to_datetime(df[candidate_cols[0]] + " " + df[candidate_cols[1]], utc=True, errors="coerce")
            time_col = "__dt"
        else:
            raise ValueError("Could not find timestamp column in Pandora CSV")
    df["time"] = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    # Value column heuristic
    val_col = None
    for c in df.columns:
        lc = str(c).lower()
        if lc in {"value", "measurement", "no2", "o3", "hcho"}:
            val_col = c
            break
    if val_col is None:
        # pick first numeric column
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            raise ValueError("No numeric value column found in Pandora CSV")
        val_col = numeric_cols[0]
    # Coordinates if present
    lat_col = next((c for c in df.columns if str(c).lower() in {"lat", "latitude"}), None)
    lon_col = next((c for c in df.columns if str(c).lower() in {"lon", "longitude"}), None)
    # Build dataset
    obs = np.arange(len(df))
    ds = xr.Dataset(
        {
            "value": ("obs", df[val_col].astype(float).to_numpy()),
        },
        coords={
            "obs": obs,
            "time": ("obs", df["time"].to_numpy()),
        },
    )
    if lat_col and lon_col:
        ds = ds.assign_coords(
            lat=("obs", df[lat_col].astype(float).to_numpy()),
            lon=("obs", df[lon_col].astype(float).to_numpy()),
        )
    if parameter:
        ds = ds.assign_coords(parameter=("obs", np.array([parameter] * len(df), dtype=object)))
    # Write to Zarr
    target = get_zarr_target("pandora_latest", partitioned=False)
    ds.to_zarr(target, mode="w")
    return int(ds.sizes.get("obs", 0))


