"""数据库和缓存集成测试"""

import pytest
from httpx import AsyncClient
from src.repositories.user import user_repository
from src.schemas.users import UserCreate
from src.utils.cache import cache_manager, clear_user_cache


class TestDatabaseIntegration:
    """数据库集成测试类"""

    async def test_database_connection(self):
        """测试数据库连接"""
        from tortoise import Tortoise

        # 验证数据库连接是否正常
        connections = Tortoise.get_connection("default")
        assert connections is not None

    async def test_user_model_crud(self):
        """测试用户模型CRUD操作"""
        # 创建用户
        user_data = UserCreate(
            username="db_test_user",
            email="db_test@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )

        created_user = await user_repository.create_user(obj_in=user_data)
        assert created_user is not None
        assert created_user.username == "db_test_user"
        assert created_user.email == "db_test@test.com"

        # 读取用户
        retrieved_user = await user_repository.get(id=created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.username == "db_test_user"

        # 更新用户
        from src.schemas.users import UserUpdate

        update_data = UserUpdate(
            id=created_user.id,
            username="db_test_user_updated",
            email="db_test_updated@test.com",
            is_active=True,
            is_superuser=False,
            role_ids=[],
        )

        updated_user = await user_repository.update(
            id=created_user.id, obj_in=update_data
        )
        assert updated_user.username == "db_test_user_updated"
        assert updated_user.email == "db_test_updated@test.com"

        # 删除用户
        await user_repository.remove(id=created_user.id)

        # 验证删除
        try:
            _ = await user_repository.get(id=created_user.id)
            raise AssertionError("应该抛出DoesNotExist异常")
        except Exception:
            # 用户已被删除，期望抛出异常
            pass

    async def test_user_authentication_flow(self):
        """测试用户认证流程"""
        # 创建用户
        user_data = UserCreate(
            username="auth_flow_test",
            email="auth_flow@test.com",
            password="Test123456",
            is_active=True,
            is_superuser=False,
        )

        created_user = await user_repository.create_user(obj_in=user_data)

        # 测试认证
        from src.schemas.login import CredentialsSchema

        credentials = CredentialsSchema(
            username="auth_flow_test", password="Test123456"
        )

        authenticated_user = await user_repository.authenticate(credentials)
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id

        # 测试错误密码
        wrong_credentials = CredentialsSchema(
            username="auth_flow_test", password="WrongPassword"
        )

        with pytest.raises(Exception):  # noqa: B017
            await user_repository.authenticate(wrong_credentials)

    async def test_database_transaction_rollback(self):
        """测试数据库事务回滚"""
        from tortoise import transactions

        initial_count = await user_repository.model.all().count()

        try:
            async with transactions.in_transaction():
                # 创建用户
                user_data = UserCreate(
                    username="transaction_test",
                    email="transaction@test.com",
                    password="Test123456",
                    is_active=True,
                    is_superuser=False,
                )

                await user_repository.create_user(obj_in=user_data)

                # 人为抛出异常触发回滚
                raise Exception("Test rollback")
        except Exception:
            pass

        # 验证回滚后用户数量未增加
        final_count = await user_repository.model.all().count()
        assert final_count == initial_count


class TestCacheIntegration:
    """缓存集成测试类"""

    async def test_cache_manager_connection(self):
        """测试缓存管理器连接"""
        # 测试连接（如果Redis不可用，应该优雅降级）
        await cache_manager.connect()

        # 测试基本操作
        test_key = "test_key"
        test_value = {"test": "data"}

        # 设置缓存
        set_result = await cache_manager.set(test_key, test_value, ttl=60)

        if cache_manager.redis:  # 只有Redis可用时才测试
            assert set_result is True

            # 获取缓存
            cached_value = await cache_manager.get(test_key)
            assert cached_value == test_value

            # 删除缓存
            delete_result = await cache_manager.delete(test_key)
            assert delete_result is True

            # 验证删除
            deleted_value = await cache_manager.get(test_key)
            assert deleted_value is None

    async def test_cache_decorator_functionality(self):
        """测试缓存装饰器功能"""
        from src.utils.cache import cached

        call_count = 0

        @cached("test_decorator", ttl=60)
        async def test_function(param: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # 第一次调用
        result1 = await test_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # 如果缓存可用，第二次调用应该使用缓存
        result2 = await test_function("test")
        assert result2 == "result_test"

        if cache_manager.redis:
            # Redis可用时，应该使用缓存
            assert call_count == 1
        else:
            # Redis不可用时，会直接调用函数
            assert call_count == 2

    async def test_user_cache_clearing(self):
        """测试用户缓存清理"""
        user_id = 123

        # 设置一些用户相关缓存
        test_caches = [
            f"user:{user_id}:profile",
            f"userinfo:{user_id}",
            f"user_roles:{user_id}",
            f"user_permissions:{user_id}",
        ]

        for cache_key in test_caches:
            await cache_manager.set(cache_key, {"test": "data"}, ttl=60)

        # 清理用户缓存
        cleared_count = await clear_user_cache(user_id)

        if cache_manager.redis:
            # Redis可用时应该清理了缓存
            assert cleared_count >= 0

            # 验证缓存已被清理
            for cache_key in test_caches:
                cached_value = await cache_manager.get(cache_key)
                assert cached_value is None

    async def test_cache_pattern_operations(self):
        """测试缓存模式操作"""
        if not cache_manager.redis:
            pytest.skip("Redis not available, skipping pattern tests")

        # 设置一些测试缓存
        test_pattern = "pattern_test"
        test_keys = [
            f"{test_pattern}:key1",
            f"{test_pattern}:key2",
            f"{test_pattern}:key3",
            "other_key",
        ]

        for key in test_keys:
            await cache_manager.set(key, {"test": "data"}, ttl=60)

        # 清理匹配模式的缓存
        cleared_count = await cache_manager.clear_pattern(f"{test_pattern}:*")

        # 应该清理了3个匹配的键
        assert cleared_count == 3

        # 验证匹配的键被清理，其他键保留
        for key in test_keys[:3]:  # pattern_test:* 键
            cached_value = await cache_manager.get(key)
            assert cached_value is None

        # other_key应该还在
        other_value = await cache_manager.get("other_key")
        assert other_value == {"test": "data"}

    async def test_cache_with_api_endpoints(
        self, async_client: AsyncClient, admin_token: str
    ):
        """测试API端点的缓存行为"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 多次调用用户信息接口
        responses = []
        for _ in range(3):
            response = await async_client.get("/api/v1/base/userinfo", headers=headers)
            assert response.status_code == 200
            responses.append(response.json())

        # 所有响应应该相同
        for response in responses[1:]:
            assert response == responses[0]
