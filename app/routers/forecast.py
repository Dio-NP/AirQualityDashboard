from fastapi import APIRouter, Query
from pydantic import BaseModel
from services.model_xgb import predict_stub, train_from_zarr, batch_predict_from_zarr, timeline_forecast
from services.model_lstm import train_lstm_from_zarr, predict_lstm_timeline
from services.explain import explain_xgb
from services.storage import get_zarr_target
from services.cache import cache_get, cache_set
from services.aqi import categorize_aqi

router = APIRouter()


class PredictRequest(BaseModel):
    no2: float | None = None
    pm25: float | None = None
    o3: float | None = None
    temperature: float | None = None
    humidity: float | None = None
    lat: float | None = None
    lon: float | None = None
    parameter_id: float | None = None
    hour: float | None = None
    weekday: float | None = None


@router.post("/forecast/predict")
async def forecast_predict(payload: PredictRequest) -> dict:
    yhat = await predict_stub(payload.model_dump())
    return {"aqi_prediction": yhat}


@router.post("/forecast/train")
def forecast_train(zarr_name: str = Query(default="openaq_latest")) -> dict:
    path = get_zarr_target(zarr_name)
    result = train_from_zarr(path)
    return result


@router.get("/forecast/batch_predict")
def forecast_batch_predict(zarr_name: str = Query(default="openaq_latest")) -> dict:
    path = get_zarr_target(zarr_name)
    result = batch_predict_from_zarr(path)
    return result


@router.get("/forecast/timeline")
def forecast_timeline(lat: float, lon: float, parameter_id: float = 0.0, hours: int = 24) -> dict:
    key = f"timeline:{lat:.3f}:{lon:.3f}:{hours}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    data = timeline_forecast(lat=lat, lon=lon, parameter_id=parameter_id, hours=hours)
    cache_set(key, data, ttl_seconds=120)
    return data


@router.get("/forecast/aqi/timeline")
def forecast_aqi_timeline(lat: float, lon: float, hours: int = 24) -> dict:
    key = f"aqi_timeline:{lat:.3f}:{lon:.3f}:{hours}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    # Use model timeline forecast (AQI-like scale 0-500) and map to categories
    raw = timeline_forecast(lat=lat, lon=lon, parameter_id=0.0, hours=hours)
    categories = [categorize_aqi(float(v)) for v in raw.get("mean", [])]
    out = {
        "times": raw.get("times", []),
        "aqi_mean": raw.get("mean", []),
        "aqi_lower": raw.get("lower", []),
        "aqi_upper": raw.get("upper", []),
        "categories": categories,
        "provenance": {
            "model": "xgb_timeline_baseline_or_trained",
            "sources": [
                {"name": "TEMPO", "variables": ["NO2", "HCHO", "AI"], "version": "settings.tempo_version_standard/NRT"},
                {"name": "OpenAQ", "variables": ["PM2.5", "NO2", "O3"]},
                {"name": "AirNow", "variables": ["PM2.5", "O3"]},
                {"name": "HRRR/MERRA-2", "variables": ["T2M", "U10M", "V10M", "RH", "PBLH"]},
                {"name": "IMERG", "variables": ["precip"], "product": "GPM_3IMERGHH_*"},
            ],
        },
    }
    cache_set(key, out, ttl_seconds=180)
    return out


@router.post("/forecast/lstm/train")
def forecast_lstm_train(zarr_name: str = Query(default="openaq_latest"), window: int = 24, horizon: int = 24, epochs: int = 5) -> dict:
    path = get_zarr_target(zarr_name)
    return train_lstm_from_zarr(path, window=window, horizon=horizon, epochs=epochs)


@router.get("/forecast/lstm/timeline")
def forecast_lstm_timeline(lat: float, lon: float, horizon: int = 24, baseline: float | None = None) -> dict:
    key = f"lstm:{lat:.3f}:{lon:.3f}:{horizon}:{baseline if baseline is not None else 'na'}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    data = predict_lstm_timeline(lat=lat, lon=lon, horizon=horizon, baseline=baseline)
    cache_set(key, data, ttl_seconds=180)
    return data


@router.post("/forecast/explain")
def forecast_explain(payload: PredictRequest) -> dict:
    return explain_xgb(payload.model_dump())
