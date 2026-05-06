"""Worker 进程的启动 / 关闭钩子。

worker 是独立进程，不会执行 FastAPI 的 lifespan，因此必须在 on_startup 中
手动初始化 Tortoise（任务里访问 ORM 才不会报 "Tortoise has not been initialized"）
和 cache_manager。
"""

from __future__ import annotations

from tortoise import Tortoise

from log import logger
from settings.config import settings
from utils.cache import cache_manager


async def worker_startup(ctx: dict) -> None:
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await cache_manager.connect()
    logger.info("arq worker 启动: Tortoise + Redis 就绪")


async def worker_shutdown(ctx: dict) -> None:
    try:
        await cache_manager.disconnect()
    finally:
        await Tortoise.close_connections()
        logger.info("arq worker 关闭")
