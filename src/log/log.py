import json
import logging
import os
import sys
from datetime import date, datetime
from typing import Any

from loguru import logger as loguru_logger

from settings import settings

LOGGING_RESERVED_FIELDS: set[str] = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}


class InterceptHandler(logging.Handler):
    """将标准 logging 日志转发到 loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - 直接调用
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in LOGGING_RESERVED_FIELDS
        }

        loguru_logger.bind(**extra).opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class LoggingConfig:
    """统一日志配置管理"""

    def __init__(self) -> None:
        self.debug = settings.DEBUG
        self.level = "DEBUG" if self.debug else "INFO"
        self.log_dir = settings.LOGS_ROOT if hasattr(settings, "LOGS_ROOT") else "logs"
        self.service_name = getattr(settings, "PROJECT_NAME", "application")
        self.environment = getattr(settings, "APP_ENV", "development")
        self.ensure_log_dir()

    def ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    @staticmethod
    def _json_default(value: Any) -> Any:
        """JSON序列化的默认处理逻辑"""
        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, set | tuple):
            return list(value)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)

    def _build_log_entry(self, record: dict[str, Any]) -> dict[str, Any]:
        """构建标准化的日志结构"""
        extra: dict[str, Any] = dict(record.get("extra", {}))
        # 避免递归引用
        extra.pop("serialized", None)

        log_entry: dict[str, Any] = {
            "timestamp": record["time"].astimezone().isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "logger": record["name"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "process": record["process"].id,
            "thread": record["thread"].id,
            "service": self.service_name,
            "environment": self.environment,
        }

        # 支持上下文透传，兼容 request_id / user_id 等字段
        context = extra.pop("context", None)
        if isinstance(context, dict):
            extra.update(context)

        log_entry.update(extra)

        if record.get("exception"):
            exception = record["exception"]
            log_entry["exception"] = {
                "type": exception.type.__name__ if exception.type else None,
                "value": str(exception.value),
                "traceback": exception.traceback,
            }

        return log_entry

    def _serialize_record(self, record: dict[str, Any]) -> str:
        """序列化日志记录为 JSON 字符串"""
        log_entry = self._build_log_entry(record)
        return json.dumps(
            log_entry,
            ensure_ascii=False,
            default=self._json_default,
            sort_keys=self.debug,
            separators=(",", ":") if not self.debug else (",", ": "),
        )

    def _patch_record(self, record: dict[str, Any]) -> None:
        """为每条日志记录附加序列化后的内容"""
        record.setdefault("extra", {})
        record["extra"]["serialized"] = self._serialize_record(record)

    def setup_logger(self):
        """配置日志输出"""
        # 清除默认处理器
        loguru_logger.remove()

        # 拦截标准 logging，统一输出格式
        intercept_handler = InterceptHandler()
        logging.basicConfig(handlers=[intercept_handler], level=0, force=True)

        for logger_name in (
            "uvicorn",
            "uvicorn.error",
            "uvicorn.access",
            "fastapi",
        ):
            standard_logger = logging.getLogger(logger_name)
            standard_logger.handlers = [intercept_handler]
            standard_logger.propagate = False

        # 启用统一 patcher，确保所有日志输出为 JSON 结构
        loguru_logger.configure(patcher=self._patch_record)

        # 控制台输出（JSON 流）
        loguru_logger.add(
            sink=sys.stdout,
            level=self.level,
            format="{extra[serialized]}",
            colorize=False,
            backtrace=True,
            diagnose=self.debug,
            enqueue=True,
        )

        # 文件输出 - 所有级别日志
        loguru_logger.add(
            sink=f"{self.log_dir}/backend_{{time:YYYY-MM-DD}}.log",
            level="DEBUG",
            format="{extra[serialized]}",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=self.debug,
            enqueue=True,
        )

        # 错误日志单独文件
        loguru_logger.add(
            sink=f"{self.log_dir}/backend_error_{{time:YYYY-MM-DD}}.log",
            level="ERROR",
            format="{extra[serialized]}",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=self.debug,
            enqueue=True,
        )

        # 关键错误日志（CRITICAL级别）
        loguru_logger.add(
            sink=f"{self.log_dir}/backend_critical_{{time:YYYY-MM-DD}}.log",
            level="CRITICAL",
            format="{extra[serialized]}",
            rotation="10 MB",
            retention="180 days",
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=self.debug,
            enqueue=True,
        )

        # 为所有日志添加默认上下文
        # 注意：这里重新绑定会创建新的logger实例

        # 记录日志系统启动
        loguru_logger.bind(event="logger_startup").info("日志系统已启动")

        return loguru_logger


# 全局日志配置实例
logging_config = LoggingConfig()
logger = logging_config.setup_logger()
