"""arq 任务队列查询路由（仅 superuser）。"""

from __future__ import annotations

from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, HTTPException, Path

from core.dependency import AuthControl
from models.admin import User
from schemas.base import Success
from tasks.queue import get_pool

router = APIRouter()


async def _require_superuser(user: User = Depends(AuthControl.is_authed)) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="仅超级管理员可访问")
    return user


@router.get(
    "/{job_id}",
    summary="查询 arq 任务状态",
    dependencies=[Depends(_require_superuser)],
)
async def get_job_status(
    job_id: str = Path(..., description="任务 ID"),
):
    pool = await get_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="任务队列不可用")

    job = Job(job_id, redis=pool)
    status: JobStatus = await job.status()
    info = await job.info()

    result_payload = None
    if status == JobStatus.complete:
        try:
            result_payload = await job.result(timeout=0.1)
        except Exception as e:
            result_payload = {"error": str(e)}

    return Success(
        data={
            "job_id": job_id,
            "status": status.value,
            "function": info.function if info else None,
            "enqueue_time": info.enqueue_time.isoformat() if info else None,
            "args": list(info.args) if info else None,
            "kwargs": dict(info.kwargs) if info else None,
            "result": result_payload,
        }
    )
