from __future__ import annotations
from typing import Optional
from pathlib import Path
import tempfile
import xarray as xr

from services.harmony_subset import subset_harmony
from services.storage import get_zarr_target, ensure_dir


def _select_tempo_variable(ds: xr.Dataset) -> str:
    # Try to find a representative TEMPO variable (NO2 or general column density)
    candidates = [
        "nitrogendioxide_tropospheric_column",
        "tropospheric_vertical_column",
        "no2",
        "NO2",
    ]
    for v in candidates:
        if v in ds:
            return v
    # fallback: first data var
    if len(ds.data_vars) == 0:
        raise ValueError("No data variables found in TEMPO subset file")
    return list(ds.data_vars.keys())[0]


async def ingest_tempo_harmony(
    collection: Optional[str] = None,
    bbox: Optional[str] = None,
    time_range: Optional[str] = None,
    zarr_name: str = "tempo_latest",
) -> int:
    coll = collection or "TEMPO_NO2_L3"
    # Download a subset NetCDF using Harmony
    tmpdir = Path(tempfile.gettempdir()) / "tempo_harmony"
    ensure_dir(tmpdir)
    nc_path = str((tmpdir / "tempo_subset.nc").resolve())
    res = subset_harmony(collection=coll, bbox=bbox, time_range=time_range, output=nc_path)
    if not res or res.get("downloaded", 0) == 0:
        return 0
    ds = xr.open_dataset(nc_path, engine="netcdf4")
    var = _select_tempo_variable(ds)
    slim = ds[[var]].rename({var: "no2"})
    # Attach simple provenance
    slim.attrs["source"] = "TEMPO"
    slim.attrs["collection"] = coll
    if bbox:
        slim.attrs["bbox"] = bbox
    if time_range:
        slim.attrs["time_range"] = time_range
    target = get_zarr_target(zarr_name, partitioned=False)
    slim.to_zarr(target, mode="w")
    return int(slim["no2"].size)


