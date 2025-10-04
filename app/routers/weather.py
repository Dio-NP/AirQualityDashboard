from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from services.merra2 import ingest_merra2
from services.hrrr_stub import ingest_hrrr_stub
from services.harmony_subset import subset_harmony

router = APIRouter()


@router.post("/ingest/merra2")
async def ingest_merra2_endpoint(
    product: Optional[str] = Query(default=None, description="MERRA-2 product short name"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    if background_tasks:
        background_tasks.add_task(ingest_merra2, product, time_range)
        return {"status": "scheduled"}
    count = await ingest_merra2(product=product, time_range=time_range)
    return {"ingested_records": count}


@router.post("/ingest/hrrr")
async def ingest_hrrr_endpoint(background_tasks: BackgroundTasks | None = None) -> dict:
    if background_tasks:
        background_tasks.add_task(ingest_hrrr_stub)
        return {"status": "scheduled"}
    count = await ingest_hrrr_stub()
    return {"ingested_records": count}


@router.post("/subset/harmony")
def harmony_subset(
    collection: str = Query(..., description="CMR collection short name"),
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    output: str = Query(default="./data/harmony_subset.nc"),
) -> dict:
    return subset_harmony(collection=collection, bbox=bbox, time_range=time_range, output=output)
