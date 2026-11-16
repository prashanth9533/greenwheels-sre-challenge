
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

from app.api.routes import router


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        for field in (
            "request_id",
            "driver_id",
            "event_type",
            "latency_ms",
        ):
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = value

        return json.dumps(log_data)


logger = logging.getLogger("greenwheels")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False


HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)

HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
)


app = FastAPI(
    title="Greenwheels Fleet Lease Service",
    description="SRE challenge - Fleet Lease API",
    version="1.0.0",
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request failed",
            extra={"request_id": request_id},
        )
        raise

    latency = time.perf_counter() - start_time
    latency_ms = round(latency * 1000, 2)

    route = request.scope.get("route")
    route_path = getattr(route, "path", request.url.path)

    HTTP_REQUESTS.labels(
        method=request.method,
        route=route_path,
        status=str(response.status_code),
    ).inc()

    HTTP_DURATION.labels(
        method=request.method,
        route=route_path,
    ).observe(latency)

    driver_id = getattr(request.state, "driver_id", None)
    if driver_id is None:
        driver_id = request.path_params.get("driver_id")

    event_type = getattr(request.state, "event_type", None)

    extra = {
        "request_id": request_id,
        "latency_ms": latency_ms,
    }

    if driver_id is not None:
        extra["driver_id"] = driver_id

    if event_type is not None:
        extra["event_type"] = event_type

    response.headers["X-Request-ID"] = request_id

    logger.info("HTTP request completed", extra=extra)

    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(router)
