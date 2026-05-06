import json
import logging

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from repositories import role_repository
from schemas.base import Success, SuccessExtra
from schemas.response import (
    ResponseBase,
    RoleAuthorizedResponse,
    RoleDetailResponse,
    RoleListResponse,
)
from schemas.roles import RoleCreate, RoleUpdate, RoleUpdateMenusApis
from utils.cache import clear_user_perms_cache_all

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list", summary="查看角色列表", response_model=RoleListResponse)
async def list_role(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    role_name: str = Query("", description="角色名称，用于查询"),
):
    q = Q()
    if role_name:
        q = Q(name__contains=role_name)
    total, role_objs = await role_repository.list(
        page=page, page_size=page_size, search=q
    )
    data = [await obj.to_dict() for obj in role_objs]
    result = SuccessExtra(data=data, total=total, page=page, page_size=page_size)
    return json.loads(result.body)


@router.get("/get", summary="查看角色", response_model=RoleDetailResponse)
async def get_role(
    role_id: int = Query(..., description="角色ID"),
):
    role_obj = await role_repository.get(id=role_id)
    result = Success(data=await role_obj.to_dict())
    return json.loads(result.body)


@router.post("/create", summary="创建角色", response_model=ResponseBase[None])
async def create_role(role_in: RoleCreate):
    if await role_repository.is_exist(name=role_in.name):
        raise HTTPException(
            status_code=400,
            detail="The role with this rolename already exists in the system.",
        )
    await role_repository.create(obj_in=role_in)
    result = Success(msg="Created Successfully")
    return json.loads(result.body)


@router.post("/update", summary="更新角色", response_model=ResponseBase[None])
async def update_role(role_in: RoleUpdate):
    await role_repository.update(id=role_in.id, obj_in=role_in)
    result = Success(msg="Updated Successfully")
    return json.loads(result.body)


@router.delete("/delete", summary="删除角色", response_model=ResponseBase[None])
async def delete_role(
    role_id: int = Query(..., description="角色ID"),
):
    await role_repository.remove(id=role_id)
    await clear_user_perms_cache_all()
    result = Success(msg="Deleted Success")
    return json.loads(result.body)


@router.get(
    "/authorized", summary="查看角色权限", response_model=RoleAuthorizedResponse
)
async def get_role_authorized(id: int = Query(..., description="角色ID")):
    role_obj = await role_repository.get(id=id)
    data = await role_obj.to_dict(m2m=True)
    result = Success(data=data)
    return json.loads(result.body)


@router.post("/authorized", summary="更新角色权限", response_model=ResponseBase[None])
async def update_role_authorized(role_in: RoleUpdateMenusApis):
    role_obj = await role_repository.get(id=role_in.id)
    await role_repository.update_roles(
        role=role_obj, menu_ids=role_in.menu_ids, api_infos=role_in.api_infos
    )
    result = Success(msg="Updated Successfully")
    return json.loads(result.body)
