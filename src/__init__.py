import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from tortoise import Tortoise

# Ensure the local ``core`` package can be imported when the project is not
# installed as a site package (e.g. during pytest execution).  This mirrors the
# behaviour of setting ``PYTHONPATH=src`` but keeps the fix self-contained.
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.dependency import get_current_username
from core.exceptions import SettingNotFound
from core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)

try:
    from settings.config import settings
except ImportError as e:
    raise SettingNotFound("Can not import settings") from e

from tasks.queue import close_arq_pool, init_arq_pool
from utils.cache import cache_manager


def _init_sentry() -> None:
    """初始化 Sentry SDK（仅当 SENTRY_DSN 设置时启用）"""
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            release=settings.VERSION,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[StarletteIntegration(), FastApiIntegration()],
        )
    except Exception:
        # Sentry 自身故障绝不应阻塞应用启动
        pass


_init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache_manager.connect()
    await init_arq_pool()
    await init_data()
    try:
        yield
    finally:
        await close_arq_pool()
        await cache_manager.disconnect()
        await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html(
        username: str = Depends(get_current_username),
    ):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=app.title + " - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html(username: str = Depends(get_current_username)):
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=app.title + " - ReDoc",
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def get_open_api_endpoint(
        username: str = Depends(get_current_username),
    ):
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        return openapi_schema

    register_exceptions(app)
    register_routers(app, prefix="/api")
    return app


app = create_app()
