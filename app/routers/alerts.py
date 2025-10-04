from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field, select
from typing import Optional, List
from db import get_session, init_db
from services.notify import send_email, send_sms
from auth import get_current_user, User
from services.ws_manager import manager
from pathlib import Path
from config import settings
import json
from datetime import datetime
from services.model_xgb import timeline_forecast
import os
import asyncio

router = APIRouter()


class AlertSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    email: Optional[str] = Field(default=None, index=True)
    phone: Optional[str] = Field(default=None, index=True)
    location: Optional[str] = Field(default=None)
    threshold_aqi: int = Field(default=100)
    active: bool = Field(default=True)


class CreateAlert(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    threshold_aqi: int = 100


@router.on_event("startup")
def _startup():
    init_db()


@router.post("/alerts", response_model=dict)
def create_alert(payload: CreateAlert, current_user: User = Depends(get_current_user)):
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=400, detail="Provide email or phone")
    sub = AlertSubscription(
        user_id=current_user.id,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        location=payload.location,
        threshold_aqi=payload.threshold_aqi,
        active=True,
    )
    with get_session() as s:
        s.add(sub)
        s.commit()
        s.refresh(sub)
    return {"id": sub.id}


@router.get("/alerts", response_model=List[dict])
def list_alerts(current_user: User = Depends(get_current_user)):
    with get_session() as s:
        rows = s.exec(select(AlertSubscription).where(AlertSubscription.user_id == current_user.id)).all()
        return [
            {
                "id": r.id,
                "email": r.email,
                "phone": r.phone,
                "location": r.location,
                "threshold_aqi": r.threshold_aqi,
                "active": r.active,
            }
            for r in rows
        ]


@router.delete("/alerts/{alert_id}", response_model=dict)
def delete_alert(alert_id: int, current_user: User = Depends(get_current_user)):
    with get_session() as s:
        sub = s.get(AlertSubscription, alert_id)
        if not sub or sub.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Not found")
        s.delete(sub)
        s.commit()
    return {"deleted": alert_id}


@router.post("/alerts/{alert_id}/trigger", response_model=dict)
def trigger_alert(alert_id: int, current_user: User = Depends(get_current_user)):
    with get_session() as s:
        sub = s.get(AlertSubscription, alert_id)
        if not sub or sub.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Not found")
    sent = {"email": False, "sms": False}
    if sub.email:
        try:
            send_email(to_email=sub.email, subject="Air Quality Alert", body="AQI exceeds your threshold")
            sent["email"] = True
        except Exception:
            pass
    if sub.phone:
        try:
            send_sms(to_phone=sub.phone, body="AQI alert: AQI exceeds threshold")
            sent["sms"] = True
        except Exception:
            pass
    # Broadcast over websocket
    import anyio
    async def _broadcast():
        await manager.broadcast_json({"type": "alert", "alert_id": alert_id, "location": sub.location, "threshold_aqi": sub.threshold_aqi})
    anyio.from_thread.run(_broadcast)
    return {"sent": sent}


# -----------------------
# Simple SMS alerts (no auth): JSON-backed store for quick setup
# -----------------------

SMS_STORE = Path(settings.data_dir) / "sms_alerts.json"


class SmsSub(BaseModel):
    phone: str
    lat: float
    lon: float
    threshold_aqi: int = 100
    hours_ahead: int = 12
    active: bool = True
    quiet_start_h: int | None = None  # 0-23 UTC
    quiet_end_h: int | None = None    # 0-23 UTC


def _load_sms() -> List[dict]:
    if not SMS_STORE.exists():
        return []
    try:
        return json.loads(SMS_STORE.read_text())
    except Exception:
        return []


def _save_sms(rows: List[dict]) -> None:
    SMS_STORE.parent.mkdir(parents=True, exist_ok=True)
    SMS_STORE.write_text(json.dumps(rows, indent=2))


@router.post("/alerts/sms", response_model=dict)
def sms_subscribe(payload: SmsSub) -> dict:
    rows = _load_sms()
    new_id = 1 + max([r.get("id", 0) for r in rows] or [0])
    rec = {"id": new_id, **payload.model_dump(), "created": datetime.utcnow().isoformat()}
    rows.append(rec)
    _save_sms(rows)
    return {"id": new_id}


@router.get("/alerts/sms", response_model=List[dict])
def sms_list() -> List[dict]:
    return _load_sms()


@router.delete("/alerts/sms/{sub_id}", response_model=dict)
def sms_delete(sub_id: int) -> dict:
    rows = _load_sms()
    rows = [r for r in rows if r.get("id") != sub_id]
    _save_sms(rows)
    return {"deleted": sub_id}


def _check_and_notify(row: dict) -> dict:
    lat = float(row.get("lat"))
    lon = float(row.get("lon"))
    hours = int(row.get("hours_ahead", 12))
    threshold = int(row.get("threshold_aqi", 100))
    # Quiet hours in UTC
    now_utc = datetime.utcnow()
    qstart = row.get("quiet_start_h")
    qend = row.get("quiet_end_h")
    if qstart is not None and qend is not None:
        h = now_utc.hour
        if qstart <= qend:
            if qstart <= h < qend:
                return {"id": row.get("id"), "sent": False, "quiet": True}
        else:  # wraps midnight
            if not (qend <= h < qstart):
                return {"id": row.get("id"), "sent": False, "quiet": True}

    # Min interval between SMS
    try:
        min_interval = int(os.getenv("ALERTS_MIN_INTERVAL_MIN", "120"))
    except Exception:
        min_interval = 120
    last_sent = row.get("last_sent")
    if last_sent:
        try:
            last_dt = datetime.fromisoformat(last_sent)
            if (now_utc - last_dt).total_seconds() < min_interval * 60:
                return {"id": row.get("id"), "sent": False, "cooldown": True}
        except Exception:
            pass
    tl = timeline_forecast(lat=lat, lon=lon, parameter_id=0.0, hours=hours)
    times = tl.get("times", [])
    mean = [float(v) for v in tl.get("mean", [])]
    fired = False
    when = None
    peak = None
    for t, v in zip(times, mean):
        if v >= threshold:
            fired = True
            when = t
            peak = v
            break
    if fired:
        body = f"AQI alert: forecast {peak:.0f} at {when}. Protect your health."
        try:
            send_sms(to_phone=row.get("phone"), body=body)
            # persist last_sent
            rows = _load_sms()
            for rr in rows:
                if rr.get("id") == row.get("id"):
                    rr["last_sent"] = now_utc.isoformat()
                    break
            _save_sms(rows)
            return {"id": row.get("id"), "sent": True, "when": when, "peak": peak}
        except Exception as e:
            return {"id": row.get("id"), "sent": False, "error": str(e)}
    return {"id": row.get("id"), "sent": False}


@router.post("/alerts/sms/trigger", response_model=List[dict])
def sms_trigger(background_tasks: BackgroundTasks) -> List[dict]:
    rows = [r for r in _load_sms() if r.get("active", True)]

    results: List[dict] = []

    def _run():
        out = []
        for r in rows:
            out.append(_check_and_notify(r))
        # store last results for introspection
        (SMS_STORE.parent / "sms_alerts_last.json").write_text(json.dumps(out, indent=2))

    background_tasks.add_task(_run)
    # immediate optimistic response
    for r in rows:
        results.append({"id": r.get("id"), "queued": True})
    return results


@router.on_event("startup")
async def _start_sms_scheduler():
    try:
        minutes = int(os.getenv("ALERTS_SCHEDULE_MINUTES", "0"))
    except Exception:
        minutes = 0
    if minutes <= 0:
        return

    async def _loop():
        while True:
            try:
                active_rows = [r for r in _load_sms() if r.get("active", True)]
                for r in active_rows:
                    _check_and_notify(r)
            except Exception:
                pass
            await asyncio.sleep(max(60, minutes * 60))

    asyncio.get_event_loop().create_task(_loop())
