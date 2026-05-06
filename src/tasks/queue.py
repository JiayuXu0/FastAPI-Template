"""arq Pool 单例与 enqueue helper。

Web 进程通过 lifespan 调用 init_arq_pool / close_arq_pool；业务代码用 enqueue_task。
Worker 进程不使用此模块（它有自己的 redis 通过 WorkerSettings）。
"""

from __future__ import annotations

from arq import create_pool
from arq.connections import ArqRedis
from arq.jobs import Job

from log import logger
from settings.config import settings

_pool: ArqRedis | None = None


async def init_arq_pool() -> ArqRedis | None:
    """建立 arq Pool；Redis 不可达时返回 None，业务降级（不阻塞应用启动）。"""
    global _pool
    if _pool is not None:
        return _pool
    try:
        _pool = await create_pool(settings.ARQ_REDIS_SETTINGS)
        logger.info("arq pool 已建立")
        return _pool
    except Exception as e:
        logger.warning(f"arq pool 创建失败，任务入队功能降级: {e}")
        _pool = None
        return None


async def close_arq_pool() -> None:
    global _pool
    if _pool is None:
        return
    try:
        await _pool.close()
    except Exception as e:
        logger.warning(f"arq pool 关闭异常: {e}")
    finally:
        _pool = None


async def enqueue_task(
    task_name: str,
    *args,
    _defer_seconds: int | None = None,
    _queue_name: str | None = None,
    **kwargs,
) -> Job | None:
    """统一任务入队入口。

    Args:
        task_name: WorkerSettings.functions 中已注册的函数名
        _defer_seconds: 延迟若干秒后执行
        _queue_name: 自定义队列名（默认使用 settings.ARQ_QUEUE_NAME）

    Returns:
        Job 句柄；arq 不可用时返回 None（不抛，业务自行决定）。
    """
    pool = await init_arq_pool()
    if pool is None:
        logger.error(f"arq 不可用，丢弃任务: {task_name}")
        return None
    return await pool.enqueue_job(
        task_name,
        *args,
        _defer_by=_defer_seconds,
        _queue_name=_queue_name or settings.ARQ_QUEUE_NAME,
        **kwargs,
    )


async def get_pool() -> ArqRedis | None:
    """供路由层 / 状态查询使用，不主动重连。"""
    return _pool
