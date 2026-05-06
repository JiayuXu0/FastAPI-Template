import json

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from repositories.api import api_repository
from schemas import Success, SuccessExtra
from schemas.apis import ApiCreate, ApiUpdate
from schemas.response import ApiInfo, ApiListResponse, ResponseBase
from utils.cache import clear_user_perms_cache_all

router = APIRouter()


@router.get("/list", summary="查看API列表", response_model=ApiListResponse)
async def list_api(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    path: str = Query(None, description="API路径"),
    summary: str = Query(None, description="API简介"),
    tags: str = Query(None, description="API模块"),
):
    q = Q()
    if path:
        q &= Q(path__contains=path)
    if summary:
        q &= Q(summary__contains=summary)
    if tags:
        q &= Q(tags__contains=tags)
    total, api_objs = await api_repository.list(
        page=page, page_size=page_size, search=q, order=["tags", "id"]
    )
    data = [await obj.to_dict() for obj in api_objs]
    result = SuccessExtra(data=data, total=total, page=page, page_size=page_size)
    return json.loads(result.body)


@router.get("/get", summary="查看Api", response_model=ResponseBase[ApiInfo])
async def get_api(
    id: int = Query(..., description="Api"),
):
    api_obj = await api_repository.get(id=id)
    data = await api_obj.to_dict()
    result = Success(data=data)
    return json.loads(result.body)


@router.post("/create", summary="创建Api", response_model=ResponseBase[None])
async def create_api(
    api_in: ApiCreate,
):
    await api_repository.create(obj_in=api_in)
    await clear_user_perms_cache_all()
    result = Success(msg="Created Successfully")
    return json.loads(result.body)


@router.post("/update", summary="更新Api", response_model=ResponseBase[None])
async def update_api(
    api_in: ApiUpdate,
):
    await api_repository.update(id=api_in.id, obj_in=api_in)
    await clear_user_perms_cache_all()
    result = Success(msg="Update Successfully")
    return json.loads(result.body)


@router.delete("/delete", summary="删除Api", response_model=ResponseBase[None])
async def delete_api(
    api_id: int = Query(..., description="ApiID"),
):
    await api_repository.remove(id=api_id)
    await clear_user_perms_cache_all()
    result = Success(msg="Deleted Success")
    return json.loads(result.body)


@router.post("/refresh", summary="刷新API列表", response_model=ResponseBase[None])
async def refresh_api():
    await api_repository.refresh_api()
    result = Success(msg="OK")
    return json.loads(result.body)
