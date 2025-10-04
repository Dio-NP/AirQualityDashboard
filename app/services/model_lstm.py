from __future__ import annotations
import os
from typing import Tuple
import numpy as np
import xarray as xr
from datetime import datetime, timedelta, timezone
from services.storage import get_model_path

try:
    import tensorflow as tf
except Exception as e:  # pragma: no cover
    tf = None

LSTM_NAME = "lstm_aqi.keras"


def _load_series_from_zarr(zarr_path: str) -> np.ndarray:
    ds = xr.open_zarr(zarr_path)
    if "value" not in ds:
        raise ValueError("Dataset missing 'value' variable")
    y = ds["value"].values.astype(float)
    y = y[np.isfinite(y)]
    return y


def _make_sequences(series: np.ndarray, window: int = 24, horizon: int = 24) -> Tuple[np.ndarray, np.ndarray]:
    X, Y = [], []
    n = len(series)
    if n < window + horizon + 1:
        raise ValueError("Not enough samples for LSTM training")
    for i in range(n - window - horizon):
        X.append(series[i:i+window])
        Y.append(series[i+window:i+window+horizon])
    X = np.array(X, dtype=np.float32)[..., None]
    Y = np.array(Y, dtype=np.float32)
    return X, Y


def train_lstm_from_zarr(zarr_path: str, window: int = 24, horizon: int = 24, epochs: int = 5) -> dict:
    if tf is None:
        raise RuntimeError("TensorFlow not installed")
    series = _load_series_from_zarr(zarr_path)
    X, Y = _make_sequences(series, window=window, horizon=horizon)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(window, 1)),
        tf.keras.layers.LSTM(64, return_sequences=False),
        tf.keras.layers.Dense(horizon)
    ])
    model.compile(optimizer="adam", loss="mae")
    model.fit(X, Y, epochs=epochs, batch_size=64, verbose=0)
    model_path = get_model_path(LSTM_NAME)
    model.save(model_path)
    return {"model_path": str(model_path), "samples": int(len(X))}


def predict_lstm_timeline(lat: float, lon: float, horizon: int = 24, window: int = 24, baseline: float | None = None) -> dict:
    now = datetime.now(timezone.utc)
    times = [now + timedelta(hours=i) for i in range(horizon)]
    model_path = get_model_path(LSTM_NAME)
    if tf is None or not os.path.exists(model_path):
        # Fallback: simple sinusoid baseline
        base = baseline if baseline is not None else 50.0
        mean = base + 20.0 * np.sin(np.linspace(0, 2*np.pi, horizon))
        spread = np.clip(0.15 * mean + 5.0, 5.0, 80.0)
        lower = np.clip(mean - spread, 0, 500)
        upper = np.clip(mean + spread, 0, 500)
        return {
            "times": [t.isoformat() for t in times],
            "mean": mean.tolist(),
            "lower": lower.tolist(),
            "upper": upper.tolist(),
            "model": "baseline"
        }
    model = tf.keras.models.load_model(model_path)
    # Build a synthetic input window around baseline (could be improved with real recent series)
    seed = np.full((1, window, 1), fill_value=(baseline if baseline is not None else 50.0), dtype=np.float32)
    pred = model.predict(seed, verbose=0)[0]
    pred = np.clip(pred, 0, 500)
    spread = np.clip(0.12 * pred + 4.0, 4.0, 70.0)
    lower = np.clip(pred - spread, 0, 500)
    upper = np.clip(pred + spread, 0, 500)
    return {
        "times": [t.isoformat() for t in times],
        "mean": pred.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "model": "lstm"
    }
