from fastapi import APIRouter, Query
import numpy as np
import xarray as xr
from services.storage import get_zarr_target
from services.collocate import collocate, collocate_points_with_grid, compute_metrics

router = APIRouter()


@router.get("/collocate")
def collocate_datasets(
    ds_a: str = Query(default="openaq_latest"),
    ds_b: str = Query(default="airnow_latest"),
    max_km: float = Query(default=25.0, ge=0),
    max_minutes: int = Query(default=60, ge=0),
) -> dict:
    a_path = get_zarr_target(ds_a)
    b_path = get_zarr_target(ds_b)
    A = xr.open_zarr(a_path)
    B = xr.open_zarr(b_path)
    C = collocate(A, B, max_km=max_km, max_minutes=max_minutes)
    metrics = compute_metrics(C)
    return {"n_matches": metrics["n"], "bias": metrics["bias"], "rmse": metrics["rmse"], "corr": metrics["corr"]}


@router.get("/collocate/tempo-pandora")
def collocate_tempo_pandora(
    tempo_ds: str = Query(default="tempo_latest"),
    pandora_ds: str = Query(default="pandora_latest"),
    grid_var: str = Query(default="no2"),
    max_km: float = Query(default=25.0, ge=0),
    max_minutes: int = Query(default=60, ge=0),
) -> dict:
    tempo_path = get_zarr_target(tempo_ds)
    pandora_path = get_zarr_target(pandora_ds)
    TEMPO = xr.open_zarr(tempo_path)
    PANDORA = xr.open_zarr(pandora_path)
    C = collocate_points_with_grid(PANDORA, TEMPO, grid_var=grid_var, max_km=max_km, max_minutes=max_minutes)
    metrics = compute_metrics(C)
    return {"n_matches": metrics["n"], "bias": metrics["bias"], "rmse": metrics["rmse"], "corr": metrics["corr"]}


@router.get("/collocate/tempo-pandora.csv")
def collocate_tempo_pandora_csv(
    tempo_ds: str = Query(default="tempo_latest"),
    pandora_ds: str = Query(default="pandora_latest"),
    grid_var: str = Query(default="no2"),
    max_km: float = Query(default=25.0, ge=0),
    max_minutes: int = Query(default=60, ge=0),
) -> str:
    tempo_path = get_zarr_target(tempo_ds)
    pandora_path = get_zarr_target(pandora_ds)
    TEMPO = xr.open_zarr(tempo_path)
    PANDORA = xr.open_zarr(pandora_path)
    C = collocate_points_with_grid(PANDORA, TEMPO, grid_var=grid_var, max_km=max_km, max_minutes=max_minutes)
    # Emit simple CSV header and rows (a_value,b_value,distance_km,a_time)
    if int(C.dims.get("match", 0)) == 0:
        return "a_value,b_value,distance_km,a_time\n"
    a = C["a_value"].values
    b = C["b_value"].values
    d = C["distance_km"].values
    t = C["a_time"].values
    lines = ["a_value,b_value,distance_km,a_time"]
    for i in range(len(a)):
        lines.append(f"{float(a[i])},{float(b[i])},{float(d[i])},{np.datetime_as_string(t[i], unit='s')}")
    return "\n".join(lines)
