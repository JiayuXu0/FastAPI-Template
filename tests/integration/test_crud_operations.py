"""CRUD操作测试"""

from httpx import AsyncClient


class TestCRUDOperations:
    """CRUD操作测试类"""

    async def test_user_crud_full_cycle(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试用户CRUD完整流程"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. 创建用户
        user_data = {
            "username": "crud_test_user",
            "email": "crud_test@test.com",
            "password": "Test123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        create_response = await async_client.post(
            "/api/v1/users/create", json=user_data, headers=headers
        )

        assert create_response.status_code == 200

        # 2. 获取用户列表，验证用户已创建
        list_response = await async_client.get("/api/v1/users/list", headers=headers)

        assert list_response.status_code == 200
        users_data = list_response.json()["data"]

        # 查找创建的用户
        created_user = None
        for user in users_data:
            if user["username"] == "crud_test_user":
                created_user = user
                break

        assert created_user is not None
        assert created_user["email"] == "crud_test@test.com"
        assert created_user["is_active"] is True

        user_id = created_user["id"]

        # 3. 更新用户
        update_data = {
            "id": user_id,
            "username": "crud_test_updated",
            "email": "crud_test_updated@test.com",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        update_response = await async_client.post(
            "/api/v1/users/update", json=update_data, headers=headers
        )

        assert update_response.status_code == 200

        # 4. 验证更新
        list_response_after_update = await async_client.get(
            "/api/v1/users/list", headers=headers
        )

        users_data_updated = list_response_after_update.json()["data"]
        updated_user = None
        for user in users_data_updated:
            if user["id"] == user_id:
                updated_user = user
                break

        assert updated_user is not None
        assert updated_user["username"] == "crud_test_updated"
        assert updated_user["email"] == "crud_test_updated@test.com"

        # 5. 删除用户
        delete_response = await async_client.delete(
            f"/api/v1/users/delete?user_id={user_id}", headers=headers
        )

        assert delete_response.status_code == 200

        # 6. 验证删除
        list_response_after_delete = await async_client.get(
            "/api/v1/users/list", headers=headers
        )

        users_data_final = list_response_after_delete.json()["data"]
        deleted_user = None
        for user in users_data_final:
            if user["id"] == user_id:
                deleted_user = user
                break

        # 用户应该被删除
        assert deleted_user is None

    async def test_user_creation_validation(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试用户创建数据验证"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 测试无效数据
        invalid_cases = [
            # 缺少用户名
            {
                "email": "test@test.com",
                "password": "Test123456",
                "is_active": True,
                "is_superuser": False,
                "role_ids": [],
            },
            # 缺少邮箱
            {
                "username": "test_user",
                "password": "Test123456",
                "is_active": True,
                "is_superuser": False,
                "role_ids": [],
            },
            # 缺少密码
            {
                "username": "test_user",
                "email": "test@test.com",
                "is_active": True,
                "is_superuser": False,
                "role_ids": [],
            },
            # 无效邮箱格式
            {
                "username": "test_user",
                "email": "invalid_email",
                "password": "Test123456",
                "is_active": True,
                "is_superuser": False,
                "role_ids": [],
            },
        ]

        for invalid_data in invalid_cases:
            response = await async_client.post(
                "/api/v1/users/create", json=invalid_data, headers=headers
            )

            # 应该返回验证错误
            assert response.status_code == 422

    async def test_duplicate_user_creation(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试创建重复用户"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        user_data = {
            "username": "duplicate_test_user",
            "email": "duplicate_test@test.com",
            "password": "Test123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        # 第一次创建应该成功
        first_response = await async_client.post(
            "/api/v1/users/create", json=user_data, headers=headers
        )

        assert first_response.status_code == 200

        # 第二次创建相同邮箱的用户应该失败
        second_response = await async_client.post(
            "/api/v1/users/create", json=user_data, headers=headers
        )

        assert second_response.status_code == 400

    async def test_user_list_pagination(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试用户列表分页"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 测试分页参数
        response = await async_client.get(
            "/api/v1/users/list?page=1&page_size=5", headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_user_search_functionality(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试用户搜索功能"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 先创建一个测试用户
        user_data = {
            "username": "search_test_user",
            "email": "search_test@test.com",
            "password": "Test123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        await async_client.post("/api/v1/users/create", json=user_data, headers=headers)

        # 测试用户名搜索
        search_response = await async_client.get(
            "/api/v1/users/list?username=search_test", headers=headers
        )

        assert search_response.status_code == 200
        search_data = search_response.json()["data"]

        # 应该找到匹配的用户
        found_user = False
        for user in search_data:
            if "search_test" in user["username"]:
                found_user = True
                break

        assert found_user

    async def test_nonexistent_user_operations(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试对不存在用户的操作"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        nonexistent_id = 99999

        # 测试更新不存在的用户
        update_data = {
            "id": nonexistent_id,
            "username": "nonexistent_user",
            "email": "nonexistent@test.com",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [],
        }

        update_response = await async_client.post(
            "/api/v1/users/update", json=update_data, headers=headers
        )

        # 应该返回错误
        assert update_response.status_code in [400, 404]

        # 测试删除不存在的用户
        delete_response = await async_client.delete(
            f"/api/v1/users/delete/{nonexistent_id}", headers=headers
        )

        # 应该返回错误
        assert delete_response.status_code in [400, 404]
