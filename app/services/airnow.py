from __future__ import annotations
import httpx
import pandas as pd
import xarray as xr
import numpy as np
from typing import Optional, List
from datetime import datetime, timezone
from config import settings
from services.storage import get_zarr_target


async def fetch_airnow(
    bbox: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    parameter: Optional[str],
    api_key: Optional[str] = None,
    limit: int = 1000,
) -> pd.DataFrame:
    key = api_key or settings.airnow_api_key
    if not key:
        raise ValueError("AIRNOW_API_KEY not provided")
    params = {
        "format": "application/json",
        "API_KEY": key,
    }
    # Basic query to observations endpoint
    # AirNow APIs vary; for demo we assume bounding box/time window params
    if bbox:
        params["BBOX"] = bbox
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date
    if parameter:
        params["parameters"] = parameter
    url = "https://www.airnowapi.org/aq/data/"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    if not data:
        return pd.DataFrame(columns=[
            "datetime","parameter","value","unit","latitude","longitude","siteName","aqi"
        ])
    df = pd.DataFrame(data)
    # Normalize column names depending on response schema
    # Attempt common keys used by AirNow data API
    time_col = None
    for c in ["DateTime", "UTC", "DateObserved"]:
        if c in df.columns:
            time_col = c
            break
    if time_col is None:
        df["datetime"] = pd.NaT
    else:
        df["datetime"] = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    lat = None
    for c in ["Latitude", "lat"]:
        if c in df.columns:
            lat = c
            break
    lon = None
    for c in ["Longitude", "lon"]:
        if c in df.columns:
            lon = c
            break
    val_col = None
    for c in ["Value", "Concentration", "value"]:
        if c in df.columns:
            val_col = c
            break
    unit_col = None
    for c in ["Unit", "UnitName", "unit"]:
        if c in df.columns:
            unit_col = c
            break
    param_col = None
    for c in ["Parameter", "ParameterName", "parameter"]:
        if c in df.columns:
            param_col = c
            break
    site_col = None
    for c in ["SiteName", "StationName", "location"]:
        if c in df.columns:
            site_col = c
            break
    aqi_col = "AQI" if "AQI" in df.columns else None
    keep = {
        "datetime": "datetime",
        lat or "lat": "latitude",
        lon or "lon": "longitude",
        val_col or "value": "value",
        unit_col or "unit": "unit",
        param_col or "parameter": "parameter",
        site_col or "location": "siteName",
    }
    out = df.rename(columns=keep)
    cols = ["datetime","parameter","value","unit","latitude","longitude","siteName"]
    if aqi_col:
        out = out.rename(columns={aqi_col: "aqi"})
        cols.append("aqi")
    for c in cols:
        if c not in out.columns:
            out[c] = np.nan
    out = out[cols]
    out = out.dropna(subset=["datetime","latitude","longitude","value"])
    return out


async def ingest_airnow_to_zarr(
    bbox: Optional[str], start_date: Optional[str], end_date: Optional[str], parameter: Optional[str], limit: int = 1000
) -> int:
    df = await fetch_airnow(bbox=bbox, start_date=start_date, end_date=end_date, parameter=parameter, limit=limit)
    if df.empty:
        ds = xr.Dataset({"value": ("obs", np.array([], dtype=float))}, coords={"obs": np.array([], dtype=int)})
        target = get_zarr_target("airnow_measurements", partitioned=False)
        ds.to_zarr(target, mode="w")
        return 0
    obs_index = np.arange(len(df))
    ds = xr.Dataset(
        {"value": ("obs", df["value"].to_numpy())},
        coords={
            "obs": obs_index,
            "time": ("obs", df["datetime"].to_numpy()),
            "lat": ("obs", df["latitude"].astype(float).to_numpy()),
            "lon": ("obs", df["longitude"].astype(float).to_numpy()),
            "parameter": ("obs", df.get("parameter", pd.Series(["unknown"]).repeat(len(df))).astype(str).to_numpy()),
            "unit": ("obs", df.get("unit", pd.Series(["unknown"]).repeat(len(df))).astype(str).to_numpy()),
            "location": ("obs", df.get("siteName", pd.Series([""]).repeat(len(df))).astype(str).to_numpy()),
            "aqi": ("obs", df.get("aqi", pd.Series([np.nan]).repeat(len(df))).to_numpy()),
        },
    )
    dt = pd.to_datetime(df["datetime"].max(), utc=True).to_pydatetime()
    target = get_zarr_target("airnow_measurements", partitioned=True, dt=dt)
    ds.to_zarr(target, mode="w")
    latest = get_zarr_target("airnow_latest", partitioned=False)
    ds.to_zarr(latest, mode="w")
    return int(len(df))
