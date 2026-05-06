"""
响应适配器：将JSONResponse转换为字典格式
使得现有的服务层代码能与Pydantic响应模型兼容
"""

from typing import Any

from schemas.base import Fail, Success, SuccessExtra


def adapt_response(response: Success | Fail | SuccessExtra) -> dict[str, Any]:
    """
    将JSONResponse对象转换为字典格式
    这个函数作为过渡期的兼容层，让现有的服务层代码能与新的Pydantic响应模型配合使用

    Args:
        response: Success、Fail或SuccessExtra实例

    Returns:
        包含响应数据的字典
    """
    if hasattr(response, "body"):
        # JSONResponse对象，从body中解析内容
        import json

        return json.loads(response.body)
    else:
        # 直接返回字典内容
        return {
            "code": getattr(response, "code", 200),
            "msg": getattr(response, "msg", "OK"),
            "data": getattr(response, "data", None),
            "total": getattr(response, "total", None),
            "page": getattr(response, "page", None),
            "page_size": getattr(response, "page_size", None),
        }
