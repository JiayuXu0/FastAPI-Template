"""认证API测试"""

from httpx import AsyncClient


class TestAuthAPI:
    """认证API测试类"""

    async def test_login_success(self, async_client: AsyncClient):
        """测试成功登录"""
        # 先创建用户
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        user_data = UserCreate(
            username="login_test_user",
            email="login_test@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )

        await user_repository.create_user(obj_in=user_data)

        # 测试登录
        response = await async_client.post(
            "/api/v1/base/access_token",
            json={"username": "login_test_user", "password": "Test123456"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "username" in data["data"]
        assert "expires_in" in data["data"]
        assert data["data"]["username"] == "login_test_user"
        assert data["data"]["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """测试无效凭据登录"""
        response = await async_client.post(
            "/api/v1/base/access_token",
            json={"username": "nonexistent_user", "password": "wrong_password"},
        )

        assert response.status_code == 400 or response.status_code == 401

    async def test_login_inactive_user(self, async_client: AsyncClient):
        """测试非激活用户登录"""
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        # 创建非激活用户
        user_data = UserCreate(
            username="inactive_user",
            email="inactive@test.com",
            password="Test123456",
            is_active=False,  # 非激活状态
            is_superuser=False,
        )

        await user_repository.create_user(obj_in=user_data)

        # 尝试登录
        response = await async_client.post(
            "/api/v1/base/access_token",
            json={"username": "inactive_user", "password": "Test123456"},
        )

        assert response.status_code == 400 or response.status_code == 401

    async def test_refresh_token_success(self, async_client: AsyncClient):
        """测试刷新令牌成功"""
        # 先登录获取令牌
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        user_data = UserCreate(
            username="refresh_test_user",
            email="refresh_test@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )

        await user_repository.create_user(obj_in=user_data)

        # 登录
        login_response = await async_client.post(
            "/api/v1/base/access_token",
            json={"username": "refresh_test_user", "password": "Test123456"},
        )

        login_data = login_response.json()["data"]
        refresh_token = login_data["refresh_token"]

        # 等待1秒确保时间戳不同
        import asyncio

        await asyncio.sleep(1)

        # 使用刷新令牌获取新的令牌对
        refresh_response = await async_client.post(
            "/api/v1/base/refresh_token", json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()["data"]

        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert "expires_in" in refresh_data
        assert refresh_data["token_type"] == "bearer"

        # 新令牌应该与原令牌不同
        assert refresh_data["access_token"] != login_data["access_token"]
        assert refresh_data["refresh_token"] != login_data["refresh_token"]

    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """测试无效刷新令牌"""
        response = await async_client.post(
            "/api/v1/base/refresh_token",
            json={"refresh_token": "invalid.refresh.token"},
        )

        assert response.status_code == 401

    async def test_refresh_token_access_token_used(self, async_client: AsyncClient):
        """测试用访问令牌进行刷新操作"""
        # 先登录获取令牌
        from src.repositories.user import user_repository
        from src.schemas.users import UserCreate

        user_data = UserCreate(
            username="token_type_test_user",
            email="token_type_test@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )

        await user_repository.create_user(obj_in=user_data)

        # 登录
        login_response = await async_client.post(
            "/api/v1/base/access_token",
            json={"username": "token_type_test_user", "password": "Test123456"},
        )

        login_data = login_response.json()["data"]
        access_token = login_data["access_token"]

        # 尝试用访问令牌进行刷新（应该失败）
        refresh_response = await async_client.post(
            "/api/v1/base/refresh_token", json={"refresh_token": access_token}
        )

        assert refresh_response.status_code == 401

    async def test_get_userinfo_with_valid_token(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试使用有效令牌获取用户信息"""
        response = await async_client.get(
            "/api/v1/base/userinfo", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert "username" in data
        assert "email" in data
        assert "is_superuser" in data
        assert "is_active" in data

    async def test_get_userinfo_without_token(self, async_client: AsyncClient):
        """测试不带令牌获取用户信息"""
        response = await async_client.get("/api/v1/base/userinfo")

        assert response.status_code == 401

    async def test_get_userinfo_with_invalid_token(self, async_client: AsyncClient):
        """测试使用无效令牌获取用户信息"""
        response = await async_client.get(
            "/api/v1/base/userinfo",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
