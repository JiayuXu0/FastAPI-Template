"""arq WorkerSettings — 独立 worker 进程通过下面命令启动：

    PYTHONPATH=src uv run arq tasks.worker.WorkerSettings

新增任务后必须重启 worker；--watch src/tasks 仅在开发模式下生效。
"""

from __future__ import annotations

from arq.cron import cron

from settings.config import settings
from tasks.hooks import worker_shutdown, worker_startup
from tasks.jobs.audit_jobs import cleanup_audit_logs_task
from tasks.jobs.email_jobs import send_email_task


class WorkerSettings:
    redis_settings = settings.ARQ_REDIS_SETTINGS
    queue_name = settings.ARQ_QUEUE_NAME

    functions = [send_email_task, cleanup_audit_logs_task]

    cron_jobs = [
        # 每天 03:00 清理 90 天前的审计日志
        cron(
            cleanup_audit_logs_task,
            hour=3,
            minute=0,
            run_at_startup=False,
        ),
    ]

    on_startup = worker_startup
    on_shutdown = worker_shutdown

    max_jobs = settings.ARQ_MAX_JOBS
    job_timeout = settings.ARQ_JOB_TIMEOUT
    keep_result = settings.ARQ_KEEP_RESULT
    max_tries = 5
