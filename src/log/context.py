"""
日志上下文管理器
提供请求追踪和用户关联功能
"""

import traceback
import uuid
from contextvars import ContextVar
from typing import Any

# 延迟导入，避免循环导入
# from log import logger

# 上下文变量
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")
# 默认使用 None 而非 dict，避免 mutable default 在跨任务间被意外共享/修改
request_context_var: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_context", default=None
)


def _get_context_dict() -> dict[str, Any]:
    """安全读取 context dict，None 时返回新 dict（不写回 var）"""
    return request_context_var.get() or {}


class LogContext:
    """日志上下文管理器"""

    @staticmethod
    def generate_request_id() -> str:
        """生成唯一请求ID"""
        return str(uuid.uuid4())[:8]

    @staticmethod
    def set_request_id(request_id: str | None = None) -> str:
        """设置请求ID"""
        if not request_id:
            request_id = LogContext.generate_request_id()
        request_id_var.set(request_id)
        return request_id

    @staticmethod
    def set_user_id(user_id: str | None) -> None:
        """设置用户ID"""
        user_id_var.set(str(user_id) if user_id else "-")

    @staticmethod
    def get_request_id() -> str:
        """获取当前请求ID"""
        return request_id_var.get()

    @staticmethod
    def get_user_id() -> str:
        """获取当前用户ID"""
        return user_id_var.get()

    @staticmethod
    def set_context(key: str, value: Any) -> None:
        """设置上下文信息"""
        context = _get_context_dict()
        context[key] = value
        request_context_var.set(context)

    @staticmethod
    def get_context(key: str = None) -> Any:
        """获取上下文信息"""
        context = _get_context_dict()
        return context.get(key) if key else context

    @staticmethod
    def update_context(**kwargs) -> None:
        """批量更新上下文信息"""
        context = _get_context_dict()
        context.update(kwargs)
        request_context_var.set(context)

    @staticmethod
    def get_logger():
        """获取带上下文的logger"""
        # 延迟导入避免循环导入
        from log.log import logger

        # 获取所有上下文信息
        context = _get_context_dict()
        base_context = {
            "request_id": LogContext.get_request_id(),
            "user_id": LogContext.get_user_id(),
        }
        base_context.update(context)

        return logger.bind(**base_context)

    @staticmethod
    def clear():
        """清除上下文"""
        request_id_var.set("-")
        user_id_var.set("-")
        request_context_var.set({})


class RequestLogContext:
    """请求级别的日志上下文管理器"""

    def __init__(self, request_id: str | None = None, user_id: str | None = None):
        self.request_id = request_id
        self.user_id = user_id
        self.old_request_id = None
        self.old_user_id = None

    def __enter__(self):
        # 保存旧值
        self.old_request_id = LogContext.get_request_id()
        self.old_user_id = LogContext.get_user_id()

        # 设置新值
        LogContext.set_request_id(self.request_id)
        LogContext.set_user_id(self.user_id)

        return LogContext.get_logger()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 如果有异常，记录异常信息
        if exc_type:
            logger = LogContext.get_logger()
            logger.error(
                f"请求上下文中发生异常: {exc_type.__name__}: {exc_val}",
                extra={
                    "exception_type": exc_type.__name__,
                    "exception_msg": str(exc_val),
                    "traceback": traceback.format_exc(),
                },
            )

        # 恢复旧值
        request_id_var.set(self.old_request_id)
        user_id_var.set(self.old_user_id)
        # 清除请求级上下文
        request_context_var.set({})


# 便捷函数
def get_context_logger():
    """获取带上下文的logger"""
    return LogContext.get_logger()


def with_request_context(request_id: str | None = None, user_id: str | None = None):
    """创建请求上下文管理器"""
    return RequestLogContext(request_id, user_id)
