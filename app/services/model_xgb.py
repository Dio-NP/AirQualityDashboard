from __future__ import annotations
import os
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import xarray as xr
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from xgboost import XGBRegressor
import joblib
from datetime import datetime, timedelta, timezone
from services.storage import get_model_path

MODEL_NAME = "xgb_aqi.pkl"


def _dataset_from_zarr(zarr_path: str) -> xr.Dataset:
    return xr.open_zarr(zarr_path)


def _build_features_from_ds(ds: xr.Dataset) -> tuple[np.ndarray, np.ndarray]:
    values = ds["value"].values.astype(float)
    lats = ds["lat"].values.astype(float)
    lons = ds["lon"].values.astype(float)
    params = ds["parameter"].values.astype(str)
    times = np.array(ds["time"].values)
    param_map = {p: i for i, p in enumerate(sorted(set(params)))}
    param_ids = np.array([param_map.get(p, -1) for p in params], dtype=float)
    timestamps = np.array(times, dtype="datetime64[s]").astype("datetime64[s]")
    hours = np.array((timestamps.astype("datetime64[h]") - timestamps.astype("datetime64[D]")).astype(int))
    weekdays = np.array(((timestamps.astype("datetime64[D]") - timestamps.astype("datetime64[W]")).astype(int)))
    X = np.column_stack([lats, lons, param_ids, hours, weekdays])
    y = values
    mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
    return X[mask], y[mask]


def train_from_zarr(zarr_path: str, test_size: float = 0.2, random_state: int = 42) -> dict:
    ds = _dataset_from_zarr(zarr_path)
    X, y = _build_features_from_ds(ds)
    if len(X) < 100:
        raise ValueError("Not enough samples to train (need >= 100)")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.08, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, n_jobs=4)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    metrics = {
        "r2": float(r2_score(y_test, y_pred)),
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    model_path = get_model_path(MODEL_NAME)
    joblib.dump(model, model_path)
    return {"model_path": str(model_path), "metrics": metrics}


def load_model() -> XGBRegressor | None:
    model_path = get_model_path(MODEL_NAME)
    if not os.path.exists(model_path):
        return None
    return joblib.load(model_path)


async def predict_stub(features: Dict[str, Any]) -> float:
    model = load_model()
    if model is None:
        weights = {
            "no2": 0.4,
            "pm25": 0.4,
            "o3": 0.1,
            "temperature": 0.05,
            "humidity": 0.05,
        }
        total = 0.0
        for k, w in weights.items():
            v = features.get(k)
            if v is None:
                continue
            try:
                total += float(v) * w
            except Exception:
                continue
        return float(np.clip(total, 0, 500))
    lat = float(features.get("lat", 0.0))
    lon = float(features.get("lon", 0.0))
    param_id = float(features.get("parameter_id", 0.0))
    hour = float(features.get("hour", 12.0))
    weekday = float(features.get("weekday", 3.0))
    X = np.array([[lat, lon, param_id, hour, weekday]], dtype=float)
    yhat = float(model.predict(X)[0])
    return float(np.clip(yhat, 0, 500))


def batch_predict_from_zarr(zarr_path: str) -> dict:
    model = load_model()
    if model is None:
        raise ValueError("Model not trained")
    ds = _dataset_from_zarr(zarr_path)
    X, y = _build_features_from_ds(ds)
    yhat = model.predict(X)
    return {"n": int(len(yhat)), "mean_pred": float(np.mean(yhat)), "max_pred": float(np.max(yhat))}


def timeline_forecast(lat: float, lon: float, parameter_id: float = 0.0, hours: int = 24) -> dict:
    """Generate next `hours` forecast with realistic uncertainty bands.
    Uses trained model if available; otherwise uses location-aware realistic baseline.
    """
    now = datetime.now(timezone.utc)
    times = [now + timedelta(hours=i) for i in range(hours)]
    model = load_model()
    preds: List[float] = []
    
    # Location-based baseline AQI (more realistic than simple sine wave)
    # Urban areas typically have higher AQI
    is_urban = (lat > 25 and lat < 50 and lon > -130 and lon < -60)  # North America urban corridor
    base_aqi = 35 if is_urban else 25  # Base AQI level
    
    for t in times:
        hour = float(t.hour)
        weekday = float(t.weekday())
        if model is None:
            # More realistic AQI simulation based on:
            # 1. Time of day (rush hour peaks)
            # 2. Day of week (weekend vs weekday)
            # 3. Location (urban vs rural)
            # 4. Random weather-like variations
            
            # Rush hour effect (7-9 AM and 5-7 PM)
            rush_hour_factor = 1.0
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                rush_hour_factor = 1.4
            elif 22 <= hour or hour <= 5:  # Night time
                rush_hour_factor = 0.7
            
            # Weekend effect
            weekend_factor = 0.8 if weekday >= 5 else 1.0
            
            # Seasonal variation (simulate different seasons)
            seasonal_factor = 1.0 + 0.3 * np.sin((t.timetuple().tm_yday / 365.0) * 2 * np.pi)
            
            # Random weather-like variation
            weather_variation = np.random.normal(0, 8)
            
            # Calculate realistic AQI
            base = base_aqi * rush_hour_factor * weekend_factor * seasonal_factor + weather_variation
            preds.append(float(np.clip(base, 10, 200)))  # More realistic range
        else:
            X = np.array([[lat, lon, parameter_id, hour, weekday]], dtype=float)
            yhat = float(model.predict(X)[0])
            preds.append(float(np.clip(yhat, 0, 500)))
    
    preds = np.array(preds)
    # More realistic uncertainty bands
    spread = np.clip(0.1 * preds + 3.0, 2.0, 25.0)
    lower = np.clip(preds - spread, 0, 500)
    upper = np.clip(preds + spread, 0, 500)
    
    return {
        "times": [t.isoformat() for t in times],
        "mean": preds.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
    }
