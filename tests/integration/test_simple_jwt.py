"""简单JWT测试 - 不依赖应用配置"""

import os
import sys
from datetime import UTC, datetime, timedelta

import pytest

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schemas.login import JWTPayload  # noqa: E402
from utils.jwt import create_access_token, create_token_pair, verify_token  # noqa: E402


class TestSimpleJWT:
    """简单JWT测试类"""

    def test_create_token_pair(self):
        """测试创建Token对"""
        user_id = 1
        username = "test_user"
        is_superuser = False

        access_token, refresh_token = create_token_pair(
            user_id=user_id, username=username, is_superuser=is_superuser
        )

        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert len(access_token) > 0
        assert len(refresh_token) > 0
        assert access_token != refresh_token

    def test_verify_access_token(self):
        """测试验证访问令牌"""
        user_id = 1
        username = "test_user"
        is_superuser = True

        access_token, _ = create_token_pair(user_id, username, is_superuser)

        # 验证访问令牌
        payload = verify_token(access_token, token_type="access")

        assert payload.user_id == user_id
        assert payload.username == username
        assert payload.is_superuser == is_superuser
        assert payload.token_type == "access"

    def test_verify_refresh_token(self):
        """测试验证刷新令牌"""
        user_id = 2
        username = "refresh_user"
        is_superuser = False

        _, refresh_token = create_token_pair(user_id, username, is_superuser)

        # 验证刷新令牌
        payload = verify_token(refresh_token, token_type="refresh")

        assert payload.user_id == user_id
        assert payload.username == username
        assert payload.is_superuser == is_superuser
        assert payload.token_type == "refresh"

    def test_token_type_validation(self):
        """测试令牌类型验证"""
        user_id = 3
        username = "type_test_user"
        is_superuser = False

        access_token, refresh_token = create_token_pair(user_id, username, is_superuser)

        # 用访问令牌验证刷新令牌类型应该失败
        with pytest.raises(Exception):  # noqa: B017
            verify_token(access_token, token_type="refresh")

        # 用刷新令牌验证访问令牌类型应该失败
        with pytest.raises(Exception):  # noqa: B017
            verify_token(refresh_token, token_type="access")

    def test_expired_token(self):
        """测试过期令牌"""
        # 创建已过期的令牌
        expire = datetime.now(UTC) - timedelta(minutes=1)  # 1分钟前过期

        payload = JWTPayload(
            user_id=4,
            username="expired_user",
            is_superuser=False,
            exp=expire,
            token_type="access",
        )

        expired_token = create_access_token(data=payload)

        # 验证过期令牌应该失败
        with pytest.raises(Exception):  # noqa: B017
            verify_token(expired_token, token_type="access")

    def test_invalid_token(self):
        """测试无效令牌"""
        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):  # noqa: B017
            verify_token(invalid_token, token_type="access")
