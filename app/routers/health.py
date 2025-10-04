from fastapi import APIRouter
import importlib

router = APIRouter()


@router.get("/health")
def healthcheck() -> dict:
    deps = {}
    for m in ["xarray", "dask", "zarr", "earthaccess"]:
        try:
            mod = importlib.import_module(m)
            deps[m] = getattr(mod, "__version__", "ok")
        except Exception:
            deps[m] = None
    return {
        "status": "ok",
        "version": 1,
        "dependencies": deps,
    }
