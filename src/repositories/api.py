from fastapi.routing import APIRoute

from core.crud import CRUDBase
from log import logger
from models.admin import Api
from schemas.apis import ApiCreate, ApiUpdate
from utils.cache import clear_user_perms_cache_all


class ApiRepository(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)

    async def refresh_api(self) -> dict:
        """同步路由表 → Api 表。返回 {created, updated, deleted} 计数，
        供调用方判断是否真发生变更（init 期判断升级路径用得到）。"""
        from src import app

        routes = app.routes

        # 删除废弃API数据
        all_api_list = []
        for route in app.routes:
            # 只更新有鉴权的API
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                all_api_list.append((list(route.methods)[0], route.path_format))
        delete_api = []
        for api in await Api.all():
            if (api.method, api.path) not in all_api_list:
                delete_api.append((api.method, api.path))
        for item in delete_api:
            method, path = item
            logger.debug(f"API Deleted {method} {path}")
            await Api.filter(method=method, path=path).delete()

        created_count = 0
        updated_count = 0
        for route in routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                summary = route.summary
                tags = list(route.tags)[0]
                api_obj = await Api.filter(method=method, path=path).first()
                if api_obj:
                    await api_obj.update_from_dict(
                        {
                            "method": method,
                            "path": path,
                            "summary": summary,
                            "tags": tags,
                        }
                    ).save()
                    updated_count += 1
                else:
                    logger.debug(f"API Created {method} {path}")
                    await Api.create(
                        **{
                            "method": method,
                            "path": path,
                            "summary": summary,
                            "tags": tags,
                        }
                    )
                    created_count += 1

        # API 表变更影响所有用户的权限决策，全量失效权限缓存
        if created_count or updated_count or delete_api:
            await clear_user_perms_cache_all()

        return {
            "created": created_count,
            "updated": updated_count,
            "deleted": len(delete_api),
        }


api_repository = ApiRepository()
