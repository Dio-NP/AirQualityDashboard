from __future__ import annotations
from typing import Dict, Any
import numpy as np

try:
    import shap  # type: ignore
except Exception:  # pragma: no cover
    shap = None

from services.model_xgb import load_model


def explain_xgb(features: Dict[str, Any]) -> dict:
    model = load_model()
    if model is None or shap is None:
        return {"explainable": False}
    lat = float(features.get("lat", 0.0))
    lon = float(features.get("lon", 0.0))
    param_id = float(features.get("parameter_id", 0.0))
    hour = float(features.get("hour", 12.0))
    weekday = float(features.get("weekday", 3.0))
    X = np.array([[lat, lon, param_id, hour, weekday]], dtype=float)
    explainer = shap.Explainer(model)
    sv = explainer(X)
    values = sv.values[0].tolist() if hasattr(sv, 'values') else []
    base = float(sv.base_values[0]) if hasattr(sv, 'base_values') else 0.0
    return {
        "explainable": True,
        "base_value": base,
        "shap_values": values,
        "features": ["lat","lon","parameter_id","hour","weekday"],
    }
