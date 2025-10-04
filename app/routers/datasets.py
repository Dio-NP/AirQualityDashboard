from fastapi import APIRouter
from pathlib import Path
from config import settings
import xarray as xr

router = APIRouter()


@router.get("/datasets")
def list_datasets() -> dict:
    data_dir: Path = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    zarrs = []
    for p in data_dir.glob("**/*.zarr"):
        zarrs.append(str(p.resolve()))
    for p in data_dir.glob("*.zarr"):
        if str(p.resolve()) not in zarrs:
            zarrs.append(str(p.resolve()))
    return {"zarr_stores": zarrs}


@router.get("/datasets/stats")
def dataset_stats() -> dict:
    stats = {}
    for p in Path(settings.data_dir).glob("*.zarr"):
        try:
            ds = xr.open_zarr(str(p))
            info = {
                "variables": list(ds.data_vars.keys()),
                "dims": {k: int(v) for k, v in ds.dims.items()},
            }
            stats[str(p.name)] = info
        except Exception:
            continue
    return stats


@router.get("/datasets/meta")
def dataset_meta() -> dict:
    meta: dict[str, dict] = {}
    for p in Path(settings.data_dir).glob("*.zarr"):
        try:
            ds = xr.open_zarr(str(p))
            meta[str(p.name)] = {
                "attrs": {k: str(v) for k, v in ds.attrs.items()},
                "coords": list(ds.coords.keys()),
                "data_vars": list(ds.data_vars.keys()),
            }
        except Exception:
            continue
    return meta