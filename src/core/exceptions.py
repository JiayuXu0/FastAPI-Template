import json
import traceback

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, IntegrityError

from log import logger
from settings.config import settings


class SettingNotFound(Exception):
    pass


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    # 记录详细的错误信息到日志
    error_details = {
        "method": req.method,
        "url": str(req.url),
        "path": req.url.path,
        "query_params": dict(req.query_params),
        "client_ip": req.client.host if req.client else None,
        "user_agent": req.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "traceback": traceback.format_exc(),
    }

    # 构建详细的错误信息
    error_message = f"DoesNotExist异常: {req.method} {req.url.path} - {exc}\n"
    error_message += f"Exception Type: {type(exc).__name__}\n"
    error_message += f"Exception Message: {str(exc)}\n"
    error_message += (
        f"\nStack Trace:\n{error_details.get('traceback', 'No traceback available')}\n"
    )
    error_message += "\nRequest Context:\n"
    for key, value in error_details.items():
        if key != "traceback":
            if isinstance(value, dict):
                error_message += (
                    f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}\n"
                )
            else:
                error_message += f"  {key}: {value}\n"
    error_message += "=" * 80

    logger.error(error_message)

    # 根据环境决定错误信息详细程度
    if settings.DEBUG:
        msg = f"Object not found: {exc}, query_params: {req.query_params}"
    else:
        msg = "请求的资源不存在"

    content = {"code": 404, "msg": msg}
    return JSONResponse(content=content, status_code=404)


async def HttpExcHandle(request: Request, exc: HTTPException):
    # 记录HTTP异常详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "status_code": exc.status_code,
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc.detail),
        "traceback": traceback.format_exc(),
    }

    # 根据状态码决定日志级别
    if exc.status_code >= 500:
        logger.bind(**error_details).error(
            f"HTTP {exc.status_code}异常: {request.method} {request.url.path} - {exc.detail}"
        )
    elif exc.status_code >= 400:
        logger.bind(**error_details).warning(
            f"HTTP {exc.status_code}异常: {request.method} {request.url.path} - {exc.detail}"
        )

    if exc.status_code == 401 and exc.headers and "WWW-Authenticate" in exc.headers:
        return Response(status_code=exc.status_code, headers=exc.headers)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": exc.detail, "data": None},
    )


async def IntegrityHandle(request: Request, exc: IntegrityError):
    # 记录数据完整性错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).error(
        f"数据完整性错误: {request.method} {request.url.path} - {exc}"
    )

    # 根据环境决定错误信息详细程度
    if settings.DEBUG:
        msg = f"IntegrityError: {exc}"
    else:
        msg = "数据完整性错误，请检查输入数据"

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)


async def RequestValidationHandle(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # 记录请求验证错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).warning(
        f"请求参数验证失败: {request.method} {request.url.path} - {len(exc.errors())}个错误"
    )

    # 根据环境决定错误信息详细程度
    if settings.DEBUG:
        msg = f"RequestValidationError: {exc.errors()}"
    else:
        msg = "请求参数验证失败，请检查输入格式"

    content = {"code": 422, "msg": msg}
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(
    request: Request, exc: ResponseValidationError
) -> JSONResponse:
    # 记录响应验证错误详情
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "validation_errors": exc.errors(),
        "traceback": traceback.format_exc(),
    }

    logger.bind(**error_details).error(
        f"响应格式验证错误: {request.method} {request.url.path} - {len(exc.errors())}个错误"
    )

    # 根据环境决定错误信息详细程度
    if settings.DEBUG:
        msg = f"ResponseValidationError: {exc.errors()}"
    else:
        msg = "服务器响应格式错误"

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)


async def UnhandledExceptionHandle(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    # 记录未处理异常的详细信息
    error_details = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "exception_type": type(exc).__name__,
        "exception_msg": str(exc),
        "exception_module": getattr(exc, "__module__", "unknown"),
        "traceback": traceback.format_exc(),
    }

    # 尝试获取请求体信息（如果可能）
    try:
        if hasattr(request, "_body"):
            error_details["request_body_size"] = (
                len(request._body) if request._body else 0
            )
    except Exception:
        pass

    logger.bind(**error_details).critical(
        f"未处理的异常: {request.method} {request.url.path} - {type(exc).__name__}: {exc}"
    )

    # 根据环境决定错误信息详细程度
    if settings.DEBUG:
        msg = f"Unhandled exception: {type(exc).__name__}: {exc}"
    else:
        msg = "服务器内部错误，请稍后重试"

    content = {"code": 500, "msg": msg}
    return JSONResponse(content=content, status_code=500)
