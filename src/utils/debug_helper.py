"""
调试助手工具
用于在业务代码中添加详细的调试信息
"""

import inspect
import json
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

from log.context import LogContext


class DebugHelper:
    """调试助手类"""

    @staticmethod
    def log_function_call(
        func_name: str,
        args: tuple = (),
        kwargs: dict = None,
        result: Any = None,
        error: Exception = None,
    ):
        """记录函数调用详情"""
        logger = LogContext.get_logger()

        call_info = {
            "function_name": func_name,
            "args_count": len(args),
            "kwargs_keys": list(kwargs.keys()) if kwargs else [],
            "has_result": result is not None,
            "has_error": error is not None,
            "call_time": datetime.now().isoformat(),
        }

        # 记录参数（避免记录敏感信息）
        safe_args = []
        for _i, arg in enumerate(args):
            if isinstance(arg, str | int | float | bool):
                if len(str(arg)) < 100:  # 避免记录过长的字符串
                    safe_args.append(str(arg))
                else:
                    safe_args.append(f"<长字符串: {len(str(arg))}字符>")
            else:
                safe_args.append(f"<{type(arg).__name__} 对象>")

        call_info["safe_args"] = safe_args

        if error:
            call_info["error_type"] = type(error).__name__
            call_info["error_msg"] = str(error)
            call_info["traceback"] = traceback.format_exc()
            logger.error(f"函数调用异常: {func_name}", extra=call_info)
        else:
            logger.debug(f"函数调用: {func_name}", extra=call_info)

    @staticmethod
    def log_database_query(
        query_type: str,
        table: str,
        conditions: dict = None,
        result_count: int = None,
        duration_ms: float = None,
        error: Exception = None,
    ):
        """记录数据库查询详情"""
        logger = LogContext.get_logger()

        query_info = {
            "query_type": query_type,
            "table": table,
            "conditions": conditions or {},
            "result_count": result_count,
            "duration_ms": duration_ms,
            "query_time": datetime.now().isoformat(),
        }

        if error:
            query_info["error_type"] = type(error).__name__
            query_info["error_msg"] = str(error)
            query_info["traceback"] = traceback.format_exc()
            logger.error(f"数据库查询异常: {query_type} {table}", extra=query_info)
        else:
            logger.debug(f"数据库查询: {query_type} {table}", extra=query_info)

    @staticmethod
    def log_business_logic(
        operation: str, data: dict = None, result: Any = None, error: Exception = None
    ):
        """记录业务逻辑执行详情"""
        logger = LogContext.get_logger()

        logic_info = {
            "operation": operation,
            "input_data": data or {},
            "has_result": result is not None,
            "operation_time": datetime.now().isoformat(),
        }

        if error:
            logic_info["error_type"] = type(error).__name__
            logic_info["error_msg"] = str(error)
            logic_info["traceback"] = traceback.format_exc()
            logger.error(f"业务逻辑异常: {operation}", extra=logic_info)
        else:
            logger.debug(f"业务逻辑执行: {operation}", extra=logic_info)

    @staticmethod
    def log_external_call(
        service: str,
        endpoint: str,
        method: str = "GET",
        request_data: dict = None,
        response_data: dict = None,
        duration_ms: float = None,
        error: Exception = None,
    ):
        """记录外部服务调用详情"""
        logger = LogContext.get_logger()

        call_info = {
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "request_data": request_data or {},
            "has_response": response_data is not None,
            "duration_ms": duration_ms,
            "call_time": datetime.now().isoformat(),
        }

        if error:
            call_info["error_type"] = type(error).__name__
            call_info["error_msg"] = str(error)
            call_info["traceback"] = traceback.format_exc()
            logger.error(f"外部服务调用异常: {service} {endpoint}", extra=call_info)
        else:
            logger.debug(f"外部服务调用: {service} {endpoint}", extra=call_info)


def debug_trace(include_args: bool = False, include_result: bool = False):
    """函数调用跟踪装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = datetime.now()

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # 记录成功调用
                call_args = args if include_args else ()
                call_result = result if include_result else None

                DebugHelper.log_function_call(
                    func_name=func_name,
                    args=call_args,
                    kwargs=kwargs,
                    result=call_result,
                )

                LogContext.update_context(
                    last_function_call=func_name,
                    last_function_duration_ms=duration,
                    last_function_success=True,
                )

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # 记录异常调用
                call_args = args if include_args else ()

                DebugHelper.log_function_call(
                    func_name=func_name, args=call_args, kwargs=kwargs, error=e
                )

                LogContext.update_context(
                    last_function_call=func_name,
                    last_function_duration_ms=duration,
                    last_function_success=False,
                    last_function_error=str(e),
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = datetime.now()

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # 记录成功调用
                call_args = args if include_args else ()
                call_result = result if include_result else None

                DebugHelper.log_function_call(
                    func_name=func_name,
                    args=call_args,
                    kwargs=kwargs,
                    result=call_result,
                )

                LogContext.update_context(
                    last_function_call=func_name,
                    last_function_duration_ms=duration,
                    last_function_success=True,
                )

                return result

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000

                # 记录异常调用
                call_args = args if include_args else ()

                DebugHelper.log_function_call(
                    func_name=func_name, args=call_args, kwargs=kwargs, error=e
                )

                LogContext.update_context(
                    last_function_call=func_name,
                    last_function_duration_ms=duration,
                    last_function_success=False,
                    last_function_error=str(e),
                )

                raise

        # 检查是否是异步函数
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 便捷函数
def log_debug(message: str, **extra):
    """记录调试信息"""
    logger = LogContext.get_logger()
    logger.debug(message, extra=extra)


def log_info(message: str, **extra):
    """记录信息"""
    logger = LogContext.get_logger()
    logger.info(message, extra=extra)


def log_warning(message: str, **extra):
    """记录警告"""
    logger = LogContext.get_logger()
    logger.warning(message, extra=extra)


def log_error(message: str, error: Exception = None, **extra):
    """记录错误"""
    logger = LogContext.get_logger()

    if error:
        # 构建详细的错误信息
        error_info = f"{message}\n"
        error_info += f"Exception Type: {type(error).__name__}\n"
        error_info += f"Exception Message: {str(error)}\n"
        error_info += f"\nStack Trace:\n{traceback.format_exc()}\n"

        # 添加上下文信息
        if extra:
            error_info += "\nContext Info:\n"
            for key, value in extra.items():
                if isinstance(value, dict):
                    error_info += (
                        f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}\n"
                    )
                else:
                    error_info += f"  {key}: {value}\n"

        error_info += "=" * 80

        # 记录详细信息
        logger.error(error_info)
    else:
        logger.bind(**extra).error(message)


def log_critical(message: str, error: Exception = None, **extra):
    """记录关键错误"""
    logger = LogContext.get_logger()

    if error:
        # 构建详细的关键错误信息
        error_info = f"{message}\n"
        error_info += f"CRITICAL Exception Type: {type(error).__name__}\n"
        error_info += f"CRITICAL Exception Message: {str(error)}\n"
        error_info += f"\nCRITICAL Stack Trace:\n{traceback.format_exc()}\n"

        # 添加上下文信息
        if extra:
            error_info += "\nContext Info:\n"
            for key, value in extra.items():
                if isinstance(value, dict):
                    error_info += (
                        f"  {key}: {json.dumps(value, indent=2, ensure_ascii=False)}\n"
                    )
                else:
                    error_info += f"  {key}: {value}\n"

        error_info += "=" * 80

        # 记录关键错误信息
        logger.critical(error_info)
    else:
        logger.bind(**extra).critical(message)
