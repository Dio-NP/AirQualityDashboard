from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, PlainTextResponse, JSONResponse
from routers import health, ingest, datasets, forecast, collocate, stations, ws, air_quality
try:
    from routers import alerts, weather, auth  # optional
except Exception:  # pragma: no cover
    alerts = None
    weather = None
    auth = None
from config import settings
from logging_config import configure_logging
from db import init_db
from middleware import security_headers_middleware, rate_limit_middleware, request_id_middleware
from pathlib import Path
import os

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except Exception:  # pragma: no cover
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = 'text/plain'

configure_logging(settings.log_level)

# Prefer ORJSON when available, otherwise fall back to standard JSONResponse
# Avoid optional dependency issues with orjson by falling back to JSONResponse
try:
    import orjson  # type: ignore
    # ORJSONResponse is allowed but we already handle fallback elsewhere
    DEFAULT_RESPONSE = ORJSONResponse
except Exception:
    DEFAULT_RESPONSE = JSONResponse

app = FastAPI(title="NASA Air Quality Forecast API", default_response_class=DEFAULT_RESPONSE)

origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.middleware('http')(request_id_middleware)
app.middleware('http')(rate_limit_middleware)
app.middleware('http')(security_headers_middleware)

# Metrics
if Counter and Histogram:
    REQS = Counter('api_requests_total', 'API requests', ['method', 'path', 'status'])
    LATENCY = Histogram('api_request_latency_seconds', 'Request latency', ['method', 'path'])

    @app.middleware('http')
    async def prometheus_middleware(request: Request, call_next):
        if request.url.path == '/metrics':
            return await call_next(request)
        method = request.method
        path = request.url.path
        import time
        start = time.perf_counter()
        response: Response = await call_next(request)
        if REQS:
            REQS.labels(method, path, str(response.status_code)).inc()
        if LATENCY:
            LATENCY.labels(method, path).observe(time.perf_counter() - start)
        return response

    @app.get('/metrics')
    def metrics():
        if generate_latest:
            data = generate_latest()
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
        return PlainTextResponse('metrics unavailable', status_code=503)

# Ensure directories
Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
Path(settings.model_dir).mkdir(parents=True, exist_ok=True)

@app.middleware('http')
async def cache_control(request: Request, call_next):
    response = await call_next(request)
    if request.method == 'GET' and response.status_code == 200:
        response.headers.setdefault('Cache-Control', 'public, max-age=60')
    return response

@app.on_event("startup")
def _startup():
    init_db()

app.include_router(health.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(collocate.router, prefix="/api")
app.include_router(stations.router, prefix="/api")
app.include_router(air_quality.router, prefix="/api")
app.include_router(ws.router)
if auth:
    app.include_router(auth.router, prefix="/api")
if alerts:
    app.include_router(alerts.router, prefix="/api")
if weather:
    app.include_router(weather.router, prefix="/api")
