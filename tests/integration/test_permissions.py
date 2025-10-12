"""权限检查测试"""

from httpx import AsyncClient


class TestPermissions:
    """权限测试类"""

    async def test_superuser_required_access_with_admin(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试管理员访问需要超级用户权限的端点"""
        # 测试用户列表接口（通常需要管理员权限）
        response = await async_client.get(
            "/api/v1/users/list", headers={"Authorization": f"Bearer {admin_token}"}
        )

        # 管理员应该可以访问
        assert response.status_code == 200

    async def test_superuser_required_access_with_normal_user(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        """测试普通用户访问需要超级用户权限的端点"""
        # 普通用户尝试访问管理员接口
        response = await async_client.get(
            "/api/v1/users/list",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )

        # 普通用户应该被拒绝（403或401）
        assert response.status_code in [401, 403]

    async def test_authenticated_access_with_valid_token(
        self, async_client: AsyncClient, normal_user_token: str
    ):
        """测试普通认证用户访问需要认证的端点"""
        response = await async_client.get(
            "/api/v1/base/userinfo",
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )

        # 认证用户应该可以访问自己的信息
        assert response.status_code == 200
        data = response.json()["data"]
        assert "username" in data

    async def test_authenticated_access_without_token(self, async_client: AsyncClient):
        """测试未认证用户访问需要认证的端点"""
        response = await async_client.get("/api/v1/base/userinfo")

        # 未认证用户应该被拒绝
        assert response.status_code == 401

    async def test_public_endpoint_access(self, async_client: AsyncClient):
        """测试公开端点访问"""
        # 健康检查应该是公开的
        response = await async_client.get("/api/v1/base/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_version_endpoint_access(self, async_client: AsyncClient):
        """测试版本信息端点访问"""
        response = await async_client.get("/api/v1/base/version")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    async def test_user_crud_permissions(
        self, async_client: AsyncClient, admin_token: str, normal_user_token: str
    ):
        """测试用户CRUD操作权限"""
        # 测试创建用户（通常需要管理员权限）
        user_data = {
            "username": "permission_test_user",
            "email": "permission_test@test.com",
            "password": "Test123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        # 管理员创建用户
        admin_response = await async_client.post(
            "/api/v1/users/create",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # 管理员应该可以创建用户
        assert admin_response.status_code == 200

        # 普通用户尝试创建用户
        normal_user_data = {
            "username": "normal_user_create_test",
            "email": "normal_create@test.com",
            "password": "Test123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        normal_response = await async_client.post(
            "/api/v1/users/create",
            json=normal_user_data,
            headers={"Authorization": f"Bearer {normal_user_token}"},
        )

        # 普通用户应该被拒绝
        assert normal_response.status_code in [401, 403]

    async def test_token_validation_edge_cases(self, async_client: AsyncClient):
        """测试令牌验证边界情况"""
        test_cases = [
            "",  # 空令牌
            "Bearer",  # 只有Bearer
            "Bearer ",  # Bearer后只有空格
            "InvalidBearer token",  # 无效格式
            "Bearer invalid.token",  # 无效令牌
        ]

        for invalid_auth in test_cases:
            response = await async_client.get(
                "/api/v1/base/userinfo", headers={"Authorization": invalid_auth}
            )

            # 所有无效情况都应该返回401
            assert response.status_code == 401

    async def test_rate_limiting_login(self, async_client: AsyncClient):
        """测试登录限流（基础测试）"""
        # 多次尝试错误登录
        for _ in range(3):
            response = await async_client.post(
                "/api/v1/base/access_token",
                json={"username": "nonexistent", "password": "wrong"},
            )
            # 每次都应该返回错误
            assert response.status_code in [400, 401]

    async def test_rate_limiting_refresh(self, async_client: AsyncClient):
        """测试刷新令牌限流（基础测试）"""
        # 多次尝试无效刷新
        for _ in range(3):
            response = await async_client.post(
                "/api/v1/base/refresh_token", json={"refresh_token": "invalid.token"}
            )
            # 每次都应该返回错误
            assert response.status_code == 401
