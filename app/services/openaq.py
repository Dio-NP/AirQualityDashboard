from __future__ import annotations
import httpx
import pandas as pd
import xarray as xr
import numpy as np
from typing import Optional, List
from datetime import datetime, timezone
from config import settings
from services.storage import get_zarr_target


async def fetch_openaq_page(
    page: int, country: Optional[str], parameter: Optional[str], limit: int
) -> List[dict]:
    params = {
        "limit": limit,
        "page": page,
        "sort": "desc",
        "order_by": "datetime",
    }
    if country:
        params["country"] = country
    if parameter:
        params["parameter"] = parameter
    # Use the new OpenAQ v2 API endpoint
    url = f"{settings.openaq_base_url}/v2/measurements"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        payload = r.json()
        return payload.get("results", [])


def normalize_df(data: List[dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(columns=[
            "datetime","parameter","value","unit","latitude","longitude","location","country","city"
        ])
    df = pd.DataFrame(data)
    if "coordinates" in df.columns:
        coords = pd.json_normalize(df["coordinates"]).rename(columns={"latitude":"latitude","longitude":"longitude"})
        df = pd.concat([df.drop(columns=["coordinates"]), coords], axis=1)
    if "date" in df.columns:
        d = pd.json_normalize(df["date"])
        ts = pd.to_datetime(d.get("utc", pd.NaT), utc=True)
        df = pd.concat([df.drop(columns=["date"]), ts.rename("datetime")], axis=1)
    elif "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    keep = [
        "datetime","parameter","value","unit","latitude","longitude","location","country","city"
    ]
    for k in keep:
        if k not in df.columns:
            df[k] = np.nan
    df = df[keep].dropna(subset=["datetime","latitude","longitude","parameter","value"])
    return df


def df_to_dataset(df: pd.DataFrame) -> xr.Dataset:
    obs_index = np.arange(len(df))
    ds = xr.Dataset(
        {
            "value": ("obs", df["value"].to_numpy()),
        },
        coords={
            "obs": obs_index,
            "time": ("obs", df["datetime"].to_numpy()),
            "lat": ("obs", df["latitude"].astype(float).to_numpy()),
            "lon": ("obs", df["longitude"].astype(float).to_numpy()),
            "parameter": ("obs", df["parameter"].astype(str).to_numpy()),
            "unit": ("obs", df["unit"].astype(str).to_numpy()),
            "location": ("obs", df["location"].astype(str).to_numpy()),
            "country": ("obs", df["country"].astype(str).to_numpy()),
            "city": ("obs", df["city"].astype(str).to_numpy()),
        },
    )
    return ds


async def ingest_openaq_to_zarr(
    country: Optional[str], parameter: Optional[str], limit: int
) -> int:
    page = 1
    total = 0
    while True:
        data = await fetch_openaq_page(page=page, country=country, parameter=parameter, limit=limit)
        if not data:
            break
        df = normalize_df(data)
        if df.empty:
            break
        ds = df_to_dataset(df)
        dt = pd.to_datetime(df["datetime"].max(), utc=True).to_pydatetime()
        target = get_zarr_target("openaq_measurements", partitioned=True, dt=dt)
        mode = "w" if total == 0 and page == 1 else "a"
        ds.to_zarr(target, mode=mode, append_dim="obs")
        total += len(df)
        if len(data) < limit:
            break
        page += 1
    # Also maintain latest consolidated unpartitioned view
    if total > 0:
        target_latest = get_zarr_target("openaq_latest", partitioned=False)
        ds_latest = df_to_dataset(df)
        ds_latest.to_zarr(target_latest, mode="w")
    return total
