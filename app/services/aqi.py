from __future__ import annotations
from typing import Dict, Tuple, Optional


def _linear_scale(concentration: float, bp_lo: float, bp_hi: float, aqi_lo: int, aqi_hi: int) -> float:
    # EPA linear interpolation between breakpoints
    if bp_hi == bp_lo:
        return float(aqi_hi)
    return ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo


def categorize_aqi(aqi: float) -> str:
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy for Sensitive"
    if aqi <= 200: return "Unhealthy"
    if aqi <= 300: return "Very Unhealthy"
    return "Hazardous"


def aqi_pm25(ug_m3: float) -> float:
    # EPA 2012 PM2.5 breakpoints (24-hr), units µg/m³
    bps = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    c = max(0.0, float(ug_m3))
    for bp_lo, bp_hi, aqi_lo, aqi_hi in bps:
        if c <= bp_hi:
            return float(round(_linear_scale(c, bp_lo, bp_hi, aqi_lo, aqi_hi)))
    return 500.0


def aqi_pm10(ug_m3: float) -> float:
    # EPA PM10 (24-hr)
    bps = [
        (0, 54, 0, 50),
        (55, 154, 51, 100),
        (155, 254, 101, 150),
        (255, 354, 151, 200),
        (355, 424, 201, 300),
        (425, 504, 301, 400),
        (505, 604, 401, 500),
    ]
    c = max(0.0, float(ug_m3))
    for bp_lo, bp_hi, aqi_lo, aqi_hi in bps:
        if c <= bp_hi:
            return float(round(_linear_scale(c, bp_lo, bp_hi, aqi_lo, aqi_hi)))
    return 500.0


def aqi_o3_8h(ppm: float) -> float:
    # O3 8-hour average (ppm)
    bps = [
        (0.000, 0.054, 0, 50),
        (0.055, 0.070, 51, 100),
        (0.071, 0.085, 101, 150),
        (0.086, 0.105, 151, 200),
        (0.106, 0.200, 201, 300),
    ]
    c = max(0.0, float(ppm))
    for bp_lo, bp_hi, aqi_lo, aqi_hi in bps:
        if c <= bp_hi:
            return float(round(_linear_scale(c, bp_lo, bp_hi, aqi_lo, aqi_hi)))
    return 500.0


def aqi_no2_1h(ppb: float) -> float:
    # NO2 1-hour (ppb); AQI values defined up to 200 ppb
    bps = [
        (0, 53, 0, 50),
        (54, 100, 51, 100),
        (101, 360, 101, 150),
        (361, 649, 151, 200),
        (650, 1249, 201, 300),
        (1250, 1649, 301, 400),
        (1650, 2049, 401, 500),
    ]
    c = max(0.0, float(ppb))
    for bp_lo, bp_hi, aqi_lo, aqi_hi in bps:
        if c <= bp_hi:
            return float(round(_linear_scale(c, bp_lo, bp_hi, aqi_lo, aqi_hi)))
    return 500.0


def compute_composite_aqi(
    pollutants: Dict[str, float],
    units: Optional[Dict[str, str]] = None,
) -> Tuple[float, str, str]:
    """
    Compute overall AQI from pollutant measurements.

    pollutants: mapping like {"pm25": ug/m3, "pm10": ug/m3, "o3": ppm, "no2": ppb}
    units: optional override for units keys (pm25, pm10, o3, no2)
    Returns: (aqi_value, category, dominant_pollutant)
    """
    units = units or {}
    aqi_by_pollutant: Dict[str, float] = {}
    if "pm25" in pollutants:
        val = pollutants["pm25"]
        aqi_by_pollutant["pm25"] = aqi_pm25(val)
    if "pm10" in pollutants:
        aqi_by_pollutant["pm10"] = aqi_pm10(pollutants["pm10"])
    if "o3" in pollutants:
        # Assume 8-hour average provided in ppm
        aqi_by_pollutant["o3"] = aqi_o3_8h(pollutants["o3"])
    if "no2" in pollutants:
        aqi_by_pollutant["no2"] = aqi_no2_1h(pollutants["no2"])
    if not aqi_by_pollutant:
        return 0.0, "Unknown", ""
    dominant = max(aqi_by_pollutant.items(), key=lambda kv: kv[1])
    overall = float(dominant[1])
    return overall, categorize_aqi(overall), dominant[0]

