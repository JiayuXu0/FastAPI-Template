"""
统一响应模型定义
用于Swagger文档展示和响应数据验证
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """基础响应模型"""

    code: int = Field(default=200, description="响应状态码")
    msg: str = Field(default="OK", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @field_validator("msg", mode="before")
    @classmethod
    def set_default_msg(cls, v):
        """当msg为None时，设置默认值"""
        return "OK" if v is None else v

    class Config:
        json_schema_extra = {"example": {"code": 200, "msg": "OK", "data": None}}


class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""

    code: int = Field(default=200, description="响应状态码")
    msg: str = Field(default="OK", description="响应消息")
    data: T | None = Field(default=None, description="响应数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")

    @field_validator("msg", mode="before")
    @classmethod
    def set_default_msg(cls, v):
        """当msg为None时，设置默认值"""
        return "OK" if v is None else v

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "msg": "OK",
                "data": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
            }
        }


class ListResponse(ResponseBase[list[T]], Generic[T]):
    """列表响应模型（不分页）"""

    pass


# ============= 用户相关响应模型 =============
class UserInfo(BaseModel):
    """用户信息模型"""

    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str | None = Field(default=None, description="邮箱")
    alias: str | None = Field(default=None, description="用户昵称")
    phone: str | None = Field(default=None, description="手机号码")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否超级管理员")
    dept_id: int | None = Field(default=None, description="部门ID")
    dept_name: str | None = Field(default=None, description="部门名称")
    role_ids: list[int] = Field(default_factory=list, description="角色ID列表")
    role_names: list[str] = Field(default_factory=list, description="角色名称列表")
    created_at: datetime | None = Field(default=None, description="创建时间")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class UserListItem(BaseModel):
    """用户列表项"""

    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str | None = Field(default=None, description="邮箱")
    alias: str | None = Field(default=None, description="用户昵称")
    phone: str | None = Field(default=None, description="手机号码")
    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")
    dept_name: str | None = Field(default=None, description="部门名称")
    role_names: list[str] = Field(default_factory=list, description="角色名称列表")
    created_at: datetime | None = Field(default=None, description="创建时间")


# ============= 认证相关响应模型 =============
class TokenInfo(BaseModel):
    """令牌信息"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="Bearer", description="令牌类型")
    expires_in: int = Field(default=14400, description="过期时间（秒）")
    username: str | None = Field(default=None, description="用户名")


class CurrentUserInfo(BaseModel):
    """当前用户信息"""

    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str | None = Field(description="邮箱")
    alias: str | None = Field(description="用户昵称")
    is_superuser: bool = Field(description="是否超级管理员")
    avatar: str | None = Field(default=None, description="头像")
    roles: list[str] = Field(default_factory=list, description="角色列表")
    permissions: list[str] = Field(default_factory=list, description="权限列表")


# ============= 基础信息响应模型 =============
class HealthInfo(BaseModel):
    """健康检查信息"""

    status: str = Field(default="healthy", description="健康状态")
    timestamp: datetime = Field(description="时间戳")
    environment: str = Field(description="运行环境")
    database: str = Field(description="数据库状态")


class VersionInfo(BaseModel):
    """版本信息"""

    app_name: str = Field(description="应用名称")
    version: str = Field(description="版本号")
    api_version: str = Field(description="API版本")
    environment: str = Field(description="运行环境")


# ============= 菜单相关响应模型 =============
class MenuItem(BaseModel):
    """菜单项"""

    id: int = Field(description="菜单ID")
    name: str = Field(description="菜单名称")
    menu_type: str = Field(description="菜单类型")
    icon: str | None = Field(description="菜单图标")
    path: str | None = Field(description="菜单路径")
    component: str | None = Field(description="前端组件")
    parent_id: int | None = Field(description="父菜单ID")
    order: int = Field(default=0, description="排序")
    is_hidden: bool = Field(default=False, description="是否隐藏")
    children: list["MenuItem"] = Field(default_factory=list, description="子菜单")


# ============= 角色相关响应模型 =============
class RoleInfo(BaseModel):
    """角色信息"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    desc: str | None = Field(description="角色描述")
    menu_ids: list[int] = Field(default_factory=list, description="菜单ID列表")
    api_ids: list[int] = Field(default_factory=list, description="API权限ID列表")
    created_at: datetime | None = Field(description="创建时间")
    updated_at: datetime | None = Field(description="更新时间")


class RoleListItem(BaseModel):
    """角色列表项"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    desc: str | None = Field(description="角色描述")
    user_count: int = Field(default=0, description="用户数量")
    created_at: datetime | None = Field(description="创建时间")


class RoleAuthorizedInfo(BaseModel):
    """角色权限详情（包含完整的菜单和API信息）"""

    id: int = Field(description="角色ID")
    name: str = Field(description="角色名称")
    desc: str | None = Field(description="角色描述")
    menus: list[MenuItem] = Field(default_factory=list, description="菜单列表")
    apis: list["ApiInfo"] = Field(default_factory=list, description="API权限列表")
    created_at: datetime | None = Field(description="创建时间")
    updated_at: datetime | None = Field(description="更新时间")


# ============= 部门相关响应模型 =============
class DeptInfo(BaseModel):
    """部门信息"""

    id: int = Field(description="部门ID")
    name: str = Field(description="部门名称")
    desc: str | None = Field(description="部门描述")
    parent_id: int | None = Field(description="父部门ID")
    order: int = Field(default=0, description="排序")
    is_deleted: bool = Field(default=False, description="是否删除")
    children: list["DeptInfo"] = Field(default_factory=list, description="子部门")


# ============= API权限相关响应模型 =============
class ApiInfo(BaseModel):
    """API权限信息"""

    id: int = Field(description="API ID")
    path: str = Field(description="API路径")
    method: str = Field(description="请求方法")
    summary: str | None = Field(description="API描述")
    tags: str | None = Field(description="API标签")


# ============= 审计日志相关响应模型 =============
class AuditLogItem(BaseModel):
    """审计日志项"""

    id: int = Field(description="日志ID")
    user_id: int | None = Field(description="用户ID")
    username: str | None = Field(description="用户名")
    module: str | None = Field(description="功能模块")
    summary: str | None = Field(description="操作描述")
    method: str = Field(description="请求方法")
    path: str = Field(description="请求路径")
    status: int = Field(description="响应状态码")
    response_time: float = Field(description="响应时间（毫秒）")
    ip: str | None = Field(description="IP地址")
    created_at: datetime | None = Field(description="创建时间")


# 递归模型更新
MenuItem.model_rebuild()
DeptInfo.model_rebuild()
RoleAuthorizedInfo.model_rebuild()


# ============= 类型别名（便于使用） =============
# 用户相关
UserListResponse = PageResponse[list[UserListItem]]
UserDetailResponse = ResponseBase[UserInfo]
UserCreateResponse = ResponseBase[None]
UserUpdateResponse = ResponseBase[None]
UserDeleteResponse = ResponseBase[None]

# 认证相关
TokenResponse = ResponseBase[TokenInfo]
CurrentUserResponse = ResponseBase[CurrentUserInfo]
HealthResponse = ResponseBase[HealthInfo]
VersionResponse = ResponseBase[VersionInfo]

# 菜单相关
MenuListResponse = ResponseBase[list[MenuItem]]
MenuDetailResponse = ResponseBase[MenuItem]

# 角色相关
RoleListResponse = PageResponse[list[RoleListItem]]
RoleDetailResponse = ResponseBase[RoleInfo]
RoleAuthorizedResponse = ResponseBase[RoleAuthorizedInfo]

# 部门相关
DeptListResponse = ResponseBase[list[DeptInfo]]
DeptDetailResponse = ResponseBase[DeptInfo]

# API权限相关
ApiListResponse = PageResponse[list[ApiInfo]]

# 审计日志相关
AuditLogListResponse = PageResponse[list[AuditLogItem]]
