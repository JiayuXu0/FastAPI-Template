import ipaddress
import locale
import os
import platform
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from slowapi import Limiter
from slowapi import extension as slowapi_extension
from slowapi.util import get_remote_address
from starlette.config import Config as StarletteConfig

from core.ctx import CTX_USER_ID
from core.dependency import DependAuth
from core.metrics import db_up, redis_up, render_metrics
from models.admin import User
from repositories.user import user_repository
from schemas.base import Fail, Success
from schemas.login import (
    CredentialsSchema,
    JWTOut,
    RefreshTokenRequest,
    TokenRefreshOut,
)
from schemas.response import CurrentUserResponse, TokenResponse
from settings import settings
from utils.cache import cache_manager
from utils.jwt import create_token_pair, verify_token


class AdaptiveEnvConfig(StarletteConfig):
    def _read_file(self, file_name):
        encodings = ["utf-8", "utf-8-sig"]
        preferred = locale.getpreferredencoding(do_setlocale=False)
        if preferred and preferred.lower() not in (e.lower() for e in encodings):
            encodings.append(preferred)
        encodings.append("latin-1")  # final fallback to avoid UnicodeDecodeError

        last_error: UnicodeDecodeError | None = None
        for encoding in encodings:
            try:
                file_values: dict[str, str] = {}
                with open(file_name, encoding=encoding) as input_file:
                    for line in input_file.readlines():
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip("\"'")
                            file_values[key] = value
                return file_values
            except UnicodeDecodeError as exc:
                last_error = exc
        if last_error:
            raise last_error
        return {}


if getattr(slowapi_extension.Config, "__name__", "") != "AdaptiveEnvConfig":
    slowapi_extension.Config = AdaptiveEnvConfig

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


def apply_rate_limit(rate="5/minute"):
    """根据环境应用限流装饰器"""

    def decorator(func):
        if os.getenv("TESTING", "false").lower() == "true":
            return func  # 测试环境不应用限流
        return limiter.limit(rate)(func)

    return decorator


@router.post("/access_token", summary="获取token", response_model=TokenResponse)
@apply_rate_limit()
async def login_access_token(request: Request, credentials: CredentialsSchema):
    user: User = await user_repository.authenticate(credentials)
    await user_repository.update_last_login(user.id)

    # 创建访问令牌和刷新令牌
    access_token, refresh_token = create_token_pair(user_id=user.id)

    data = JWTOut(
        access_token=access_token,
        refresh_token=refresh_token,
        username=user.username,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return Success(data=data.model_dump())


@router.post("/refresh_token", summary="刷新token", response_model=TokenResponse)
@apply_rate_limit("10/minute")
async def refresh_access_token(request: Request, refresh_request: RefreshTokenRequest):
    """
    使用刷新令牌获取新的访问令牌和刷新令牌
    """
    try:
        # 验证刷新令牌
        payload = verify_token(refresh_request.refresh_token, token_type="refresh")

        # 验证用户是否仍然存在且有效
        user = await user_repository.get(id=payload.user_id)
        if not user or not user.is_active:
            return Fail(code=401, msg="用户不存在或已被禁用")

        # 创建新的令牌对
        access_token, refresh_token = create_token_pair(user_id=user.id)

        data = TokenRefreshOut(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return Success(data=data.model_dump())

    except Exception as exc:  # noqa: BLE001 - propagate as HTTP error for clarity
        raise HTTPException(status_code=401, detail="令牌无效或已过期") from exc


@router.get("/userinfo", summary="查看用户信息", response_model=CurrentUserResponse)
async def get_userinfo(current_user: User = DependAuth):
    user_id = CTX_USER_ID.get()
    user_obj = await user_repository.get(id=user_id)
    user_dict = await user_obj.to_dict()
    return Success(data=user_dict)


@router.get("/health", summary="健康检查")
async def health_check():
    """系统健康检查（同时刷新 redis_up / db_up 指标）"""

    redis_ok = cache_manager.is_available
    redis_up.set(1 if redis_ok else 0)

    db_ok = True
    try:
        from tortoise import Tortoise

        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
    except Exception:
        db_ok = False
    db_up.set(1 if db_ok else 0)

    return {
        "status": "healthy" if (redis_ok and db_ok) else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "service": settings.PROJECT_NAME,
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }


def _is_metrics_allowed(client_ip: str | None) -> bool:
    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    return any(addr in net for net in settings.METRICS_ALLOWED_NETWORKS)


@router.get("/metrics", summary="Prometheus 指标", include_in_schema=False)
async def metrics_endpoint(request: Request):
    """暴露 Prometheus 指标。仅放行白名单 IP（默认 localhost + 内网网段）。"""
    client_ip = request.client.host if request.client else None
    if not _is_metrics_allowed(client_ip):
        raise HTTPException(status_code=403, detail="Forbidden")
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@router.get("/version", summary="版本信息")
async def get_version():
    """获取API版本信息"""

    return {
        "version": settings.VERSION,
        "app_title": settings.APP_TITLE,
        "project_name": settings.PROJECT_NAME,
        "build": os.getenv("APP_BUILD", "dev"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "python_version": platform.python_version(),
    }


# @router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
# async def get_user_menu():
#     user_id = CTX_USER_ID.get()
#     user_obj = await User.filter(id=user_id).first()
#     menus: list[Menu] = []
#     if user_obj.is_superuser:
#         menus = await Menu.all()
#     else:
#         role_objs: list[Role] = await user_obj.roles
#         for role_obj in role_objs:
#             menu = await role_obj.menus
#             menus.extend(menu)
#         menus = list(set(menus))
#     parent_menus: list[Menu] = []
#     for menu in menus:
#         if menu.parent_id == 0:
#             parent_menus.append(menu)
#     res = []
#     for parent_menu in parent_menus:
#         parent_menu_dict = await parent_menu.to_dict()
#         parent_menu_dict["children"] = []
#         for menu in menus:
#             if menu.parent_id == parent_menu.id:
#                 parent_menu_dict["children"].append(await menu.to_dict())
#         res.append(parent_menu_dict)
#     return Success(data=res)


# @router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
# async def get_user_api():
#     user_id = CTX_USER_ID.get()
#     user_obj = await User.filter(id=user_id).first()
#     if user_obj.is_superuser:
#         api_objs: list[Api] = await Api.all()
#         apis = [api.method.lower() + api.path for api in api_objs]
#         return Success(data=apis)
#     role_objs: list[Role] = await user_obj.roles
#     apis = []
#     for role_obj in role_objs:
#         api_objs: list[Api] = await role_obj.apis
#         apis.extend([api.method.lower() + api.path for api in api_objs])
#     apis = list(set(apis))
#     return Success(data=apis)


# @router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
# async def update_user_password(req_in: UpdatePassword):
#     user_id = CTX_USER_ID.get()
#     user = await user_controller.get(user_id)
#     verified = verify_password(req_in.old_password, user.password)
#     if not verified:
#         return Fail(msg="旧密码验证错误！")
#     user.password = get_password_hash(req_in.new_password)
#     await user.save()
#     return Success(msg="修改成功")
