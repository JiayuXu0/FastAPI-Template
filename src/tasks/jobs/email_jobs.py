"""邮件类任务示例。

注意：args/kwargs/return 走 msgpack 序列化，不要传 ORM 实例 / Pydantic 模型 / datetime。
传 ID 让任务自己重新查 DB；时间用 ISO 字符串。
"""

from __future__ import annotations

from log import logger


async def send_email_task(
    ctx: dict,
    to: str,
    subject: str,
    body: str,
) -> dict:
    """发送邮件（SMTP 实现留作占位）。

    抛异常时 arq 自动重试（max_tries 在 WorkerSettings 中配置，默认 5、指数退避）。
    """
    logger.info(
        f"[arq job_id={ctx.get('job_id')} try={ctx.get('job_try')}] "
        f"send email to={to} subject={subject!r}"
    )
    # TODO: 接入 aiosmtplib / 第三方邮件服务
    # async with aiosmtplib.SMTP(...) as smtp:
    #     await smtp.send_message(...)
    return {"to": to, "subject": subject, "status": "sent"}
