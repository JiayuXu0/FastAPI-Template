"""Prometheus metrics 定义与中间件

按路由模板（route.path）打点而非原始 URL，避免高基数（路径参数会产生爆炸式 label）。
通过 settings.METRICS_ALLOWED_IPS 限制 /metrics 端点的访问源。
"""

from __future__ import annotations

import time

from fastapi.routing import APIRoute
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REGISTRY = CollectorRegistry(auto_describe=True)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "endpoint", "status"),
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "endpoint"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Currently in-progress HTTP requests (by method only — endpoint omitted to avoid high cardinality, since route template is not known before call_next)",
    labelnames=("method",),
    registry=REGISTRY,
)

redis_up = Gauge(
    "redis_up",
    "1 if Redis is reachable, 0 otherwise",
    registry=REGISTRY,
)

db_up = Gauge(
    "db_up",
    "1 if Database is reachable, 0 otherwise",
    registry=REGISTRY,
)


def _resolve_endpoint(request: Request) -> str:
    """优先取 FastAPI 路由模板（含占位符），降级到原始 path"""
    route = request.scope.get("route")
    if isinstance(route, APIRoute):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    """记录每个 HTTP 请求的耗时、状态、方法。"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        # in_progress 只带 method label（endpoint 在 call_next 前未知，
        # 用原始 path 会因路径参数产生爆炸式 series）
        in_progress = http_requests_in_progress.labels(method=method)
        in_progress.inc()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed = time.perf_counter() - start
            # endpoint 用路由模板（call_next 后 scope["route"] 才被填充）
            endpoint = _resolve_endpoint(request)
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(elapsed)
            http_requests_total.labels(
                method=method, endpoint=endpoint, status=str(status_code)
            ).inc()
            in_progress.dec()


def render_metrics() -> tuple[bytes, str]:
    """生成 Prometheus 文本格式输出（供 /metrics 端点用）"""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
