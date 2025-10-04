from __future__ import annotations
import numpy as np
import xarray as xr
from typing import Tuple
from datetime import timedelta


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def collocate(ds_a: xr.Dataset, ds_b: xr.Dataset, max_km: float = 25.0, max_minutes: int = 60) -> xr.Dataset:
    lat_a = ds_a["lat"].values
    lon_a = ds_a["lon"].values
    time_a = ds_a["time"].values.astype("datetime64[ms]")
    val_a = ds_a["value"].values

    lat_b = ds_b["lat"].values
    lon_b = ds_b["lon"].values
    time_b = ds_b["time"].values.astype("datetime64[ms]")
    val_b = ds_b["value"].values

    matches = []
    for i in range(len(lat_a)):
        dt = np.abs(time_b - time_a[i]).astype("timedelta64[m]").astype(int)
        mask_time = dt <= max_minutes
        if not np.any(mask_time):
            continue
        dists = _haversine(lat_a[i], lon_a[i], lat_b[mask_time], lon_b[mask_time])
        j_rel = np.argmin(dists)
        if dists[j_rel] <= max_km:
            j = np.nonzero(mask_time)[0][j_rel]
            matches.append((i, j))
    if not matches:
        return xr.Dataset(
            {"a_value": ("match", np.array([], dtype=float)), "b_value": ("match", np.array([], dtype=float))},
            coords={"match": np.array([], dtype=int)}
        )
    idx_a, idx_b = zip(*matches)
    out = xr.Dataset(
        {
            "a_value": ("match", val_a[list(idx_a)]),
            "b_value": ("match", val_b[list(idx_b)]),
            "distance_km": ("match", _haversine(lat_a[list(idx_a)], lon_a[list(idx_a)], lat_b[list(idx_b)], lon_b[list(idx_b)])),
        },
        coords={
            "match": np.arange(len(matches)),
            "a_time": ("match", time_a[list(idx_a)]),
            "b_time": ("match", time_b[list(idx_b)]),
        },
    )
    return out


def collocate_points_with_grid(
    ds_points: xr.Dataset,
    ds_grid: xr.Dataset,
    grid_var: str = "no2",
    max_km: float = 25.0,
    max_minutes: int = 60,
) -> xr.Dataset:
    """
    Collocate point observations (e.g., Pandora) with nearest grid cell from a gridded product (e.g., TEMPO).
    Assumes ds_points has coords: time (obs), lat (obs), lon (obs) and variable 'value'.
    Assumes ds_grid has coords: lat (y), lon (x), optionally time (t), and data variable named by grid_var.
    """
    lat_p = ds_points["lat"].values if "lat" in ds_points.coords else None
    lon_p = ds_points["lon"].values if "lon" in ds_points.coords else None
    time_p = ds_points["time"].values.astype("datetime64[ms]")
    val_p = ds_points["value"].values
    if lat_p is None or lon_p is None:
        # Cannot perform spatial collocation without coordinates
        return xr.Dataset(
            {"a_value": ("match", np.array([], dtype=float)), "b_value": ("match", np.array([], dtype=float))},
            coords={"match": np.array([], dtype=int)}
        )

    # Grid coordinates
    if "lat" not in ds_grid.coords or "lon" not in ds_grid.coords or grid_var not in ds_grid:
        return xr.Dataset(
            {"a_value": ("match", np.array([], dtype=float)), "b_value": ("match", np.array([], dtype=float))},
            coords={"match": np.array([], dtype=int)}
        )
    lat_g = ds_grid["lat"].values
    lon_g = ds_grid["lon"].values
    has_time_g = "time" in ds_grid.coords
    time_g = ds_grid["time"].values.astype("datetime64[ms]") if has_time_g else None

    matches = []
    for i in range(len(val_p)):
        # Time filter
        tmask = None
        if has_time_g:
            dt = np.abs(time_g - time_p[i]).astype("timedelta64[m]").astype(int)
            tmask = dt <= max_minutes
            if not np.any(tmask):
                continue
            # choose nearest time index
            j_t = int(np.argmin(dt))
        else:
            j_t = None

        # Nearest grid cell by index (assumes rectilinear grid)
        j_lat = int(np.argmin(np.abs(lat_g - lat_p[i])))
        j_lon = int(np.argmin(np.abs(lon_g - lon_p[i])))

        # Compute distance to verify within threshold
        dkm = _haversine(lat_p[i], lon_p[i], lat_g[j_lat], lon_g[j_lon])
        if dkm > max_km:
            continue

        # Sample grid variable
        if has_time_g and j_t is not None and grid_var in ds_grid:
            grid_val = ds_grid[grid_var].isel(time=j_t, lat=j_lat, lon=j_lon).item()
        else:
            grid_val = ds_grid[grid_var].isel(lat=j_lat, lon=j_lon).item()

        matches.append((i, float(grid_val), float(dkm)))

    if not matches:
        return xr.Dataset(
            {"a_value": ("match", np.array([], dtype=float)), "b_value": ("match", np.array([], dtype=float))},
            coords={"match": np.array([], dtype=int)}
        )

    idx_p = [m[0] for m in matches]
    grid_vals = [m[1] for m in matches]
    dists = [m[2] for m in matches]

    out = xr.Dataset(
        {
            "a_value": ("match", val_p[idx_p]),
            "b_value": ("match", np.array(grid_vals, dtype=float)),
            "distance_km": ("match", np.array(dists, dtype=float)),
        },
        coords={
            "match": np.arange(len(matches)),
            "a_time": ("match", time_p[idx_p]),
        },
    )
    return out


def compute_metrics(C: xr.Dataset) -> dict:
    n = int(C.dims.get("match", 0))
    if n == 0:
        return {"n": 0, "bias": 0.0, "rmse": 0.0, "corr": 0.0}
    a = C["a_value"].values.astype(float)
    b = C["b_value"].values.astype(float)
    bias = float(np.nanmean(b - a))
    rmse = float(np.sqrt(np.nanmean((b - a) ** 2)))
    # Pearson correlation (guard against degenerate variance)
    if np.nanstd(a) == 0 or np.nanstd(b) == 0:
        corr = 0.0
    else:
        corr = float(np.corrcoef(a, b)[0, 1])
    return {"n": n, "bias": bias, "rmse": rmse, "corr": corr}