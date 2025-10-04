from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from services.openaq import ingest_openaq_to_zarr
from services.tempo_stub import ingest_tempo_stub
from services.airnow import ingest_airnow_to_zarr
from services.imerg import ingest_imerg
from services.tempo_harmony import ingest_tempo_harmony
from services.pandora import ingest_pandora_csv

router = APIRouter()


@router.post("/ingest/openaq")
async def ingest_openaq(
    background_tasks: BackgroundTasks,
    country: Optional[str] = Query(default=None, description="ISO country code filter"),
    parameter: Optional[str] = Query(default=None, description="Pollutant parameter (e.g., pm25, no2)"),
    limit: int = Query(default=1000, ge=1, le=10000),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_openaq_to_zarr, country, parameter, limit)
        return {"status": "scheduled"}
    count = await ingest_openaq_to_zarr(country=country, parameter=parameter, limit=limit)
    return {"ingested_records": count}


@router.post("/ingest/tempo")
async def ingest_tempo(
    background_tasks: BackgroundTasks,
    product: Optional[str] = Query(default=None, description="e.g., TEMPO_NO2_L3 or TEMPO_NO2_L2_NRT"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    version: Optional[str] = Query(default=None, description="e.g., V04 for standard, V02 for NRT"),
    nrt: bool = Query(default=False, description="Use NRT products when True"),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_tempo_stub, product, time_range, version, nrt)
        return {"status": "scheduled"}
    count = await ingest_tempo_stub(product=product, time_range=time_range, version=version, nrt=nrt)
    return {"ingested_records": count}


@router.post("/ingest/tempo/earthdata")
async def ingest_tempo_earthdata(
    background_tasks: BackgroundTasks,
    product: Optional[str] = Query(default=None, description="e.g., TEMPO_NO2_L3 or TEMPO_NO2_L2_NRT"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    version: Optional[str] = Query(default=None, description="e.g., V04 for standard, V02 for NRT"),
    nrt: bool = Query(default=False, description="Use NRT products when True"),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_tempo_stub, product, time_range, version, nrt)
        return {"status": "scheduled"}
    count = await ingest_tempo_stub(product=product, time_range=time_range, version=version, nrt=nrt)
    return {"ingested_records": count}


@router.post("/ingest/airnow")
async def ingest_airnow(
    background_tasks: BackgroundTasks,
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    start_date: Optional[str] = Query(default=None, description="ISO start"),
    end_date: Optional[str] = Query(default=None, description="ISO end"),
    parameter: Optional[str] = Query(default=None, description="e.g., PM2.5, OZONE"),
    limit: int = Query(default=1000, ge=1, le=10000),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_airnow_to_zarr, bbox, start_date, end_date, parameter, limit)
        return {"status": "scheduled"}
    count = await ingest_airnow_to_zarr(bbox=bbox, start_date=start_date, end_date=end_date, parameter=parameter, limit=limit)
    return {"ingested_records": count}


@router.post("/ingest/imerg")
async def ingest_imerg_endpoint(
    background_tasks: BackgroundTasks,
    product: Optional[str] = Query(default=None, description="e.g., GPM_3IMERGHH_E (Early), GPM_3IMERGHH_L (Late), GPM_3IMERGHH (Final)"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_imerg, product, time_range)
        return {"status": "scheduled"}
    count = await ingest_imerg(product=product, time_range=time_range)
    return {"ingested_records": count}


@router.post("/ingest/tempo/harmony")
async def ingest_tempo_harmony_endpoint(
    background_tasks: BackgroundTasks,
    collection: Optional[str] = Query(default=None, description="TEMPO collection short_name, e.g., TEMPO_NO2_L3 or TEMPO_NO2_L2_NRT"),
    bbox: Optional[str] = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    time_range: Optional[str] = Query(default=None, description="ISO start,end"),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_tempo_harmony, collection, bbox, time_range)
        return {"status": "scheduled"}
    count = await ingest_tempo_harmony(collection=collection, bbox=bbox, time_range=time_range)
    return {"ingested_records": count}


@router.post("/ingest/pandora")
async def ingest_pandora_endpoint(
    background_tasks: BackgroundTasks,
    url: str = Query(description="HTTP(S) URL to a Pandora CSV export"),
    parameter: Optional[str] = Query(default=None, description="Optional pollutant name for tagging (e.g., NO2, O3, HCHO)"),
    schedule: bool = Query(default=True, description="Run ingestion in background"),
) -> dict:
    if schedule:
        background_tasks.add_task(ingest_pandora_csv, url, parameter)
        return {"status": "scheduled"}
    count = await ingest_pandora_csv(url=url, parameter=parameter)
    return {"ingested_records": count}
