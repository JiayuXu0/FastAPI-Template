"""审计日志维护类任务。"""

from __future__ import annotations

from datetime import datetime, timedelta

from log import logger
from models.admin import AuditLog


async def cleanup_audit_logs_task(ctx: dict, retention_days: int = 90) -> dict:
    """清理 N 天前的审计日志（默认 90 天）。

    供 cron 调度；手动触发也可：`enqueue_task("cleanup_audit_logs_task", retention_days=30)`。
    """
    cutoff = datetime.now() - timedelta(days=retention_days)
    deleted = await AuditLog.filter(created_at__lt=cutoff).delete()
    logger.info(
        f"[arq job_id={ctx.get('job_id')}] cleanup audit logs: "
        f"cutoff={cutoff.isoformat()} deleted={deleted}"
    )
    return {
        "deleted": deleted,
        "cutoff": cutoff.isoformat(),
        "retention_days": retention_days,
    }
