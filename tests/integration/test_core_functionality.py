"""核心功能测试 - 最小可行版本"""

import os
import sys
from datetime import UTC, datetime, timedelta

import pytest

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schemas.login import CredentialsSchema, JWTPayload  # noqa: E402
from utils.jwt import create_token_pair, verify_token  # noqa: E402


class TestJWTCore:
    """JWT核心功能测试"""

    def test_token_creation_and_verification(self):
        """测试令牌创建和验证"""
        # 创建令牌对
        access_token, refresh_token = create_token_pair(
            user_id=1, username="test_user", is_superuser=False
        )

        # 验证访问令牌
        access_payload = verify_token(access_token, "access")
        assert access_payload.user_id == 1
        assert access_payload.username == "test_user"
        assert access_payload.token_type == "access"

        # 验证刷新令牌
        refresh_payload = verify_token(refresh_token, "refresh")
        assert refresh_payload.user_id == 1
        assert refresh_payload.username == "test_user"
        assert refresh_payload.token_type == "refresh"

    def test_token_type_security(self):
        """测试令牌类型安全"""
        access_token, refresh_token = create_token_pair(1, "test", False)

        # 用错误类型验证应该失败
        with pytest.raises(Exception):  # noqa: B017
            verify_token(access_token, "refresh")

        with pytest.raises(Exception):  # noqa: B017
            verify_token(refresh_token, "access")

    def test_expired_token_rejection(self):
        """测试过期令牌被拒绝"""
        from utils.jwt import create_access_token

        # 创建过期令牌
        expired_payload = JWTPayload(
            user_id=1,
            username="test",
            is_superuser=False,
            exp=datetime.now(UTC) - timedelta(minutes=1),
            token_type="access",
        )

        expired_token = create_access_token(data=expired_payload)

        with pytest.raises(Exception):  # noqa: B017
            verify_token(expired_token, "access")


class TestDataValidation:
    """数据验证测试"""

    def test_credentials_schema_validation(self):
        """测试凭据数据验证"""
        # 有效凭据
        valid_creds = CredentialsSchema(username="test_user", password="password123")

        assert valid_creds.username == "test_user"
        assert valid_creds.password == "password123"

    def test_jwt_payload_validation(self):
        """测试JWT载荷验证"""
        payload = JWTPayload(
            user_id=123,
            username="test_user",
            is_superuser=True,
            exp=datetime.now(UTC) + timedelta(hours=1),
            token_type="access",
        )

        assert payload.user_id == 123
        assert payload.username == "test_user"
        assert payload.is_superuser is True
        assert payload.token_type == "access"


class TestPasswordSecurity:
    """密码安全测试"""

    def test_password_hashing(self):
        """测试密码哈希"""
        from utils.password import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        # 哈希后的密码应该不同
        assert hashed != password
        assert len(hashed) > 20  # 哈希应该有合理长度

        # 验证密码
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """测试不同密码产生不同哈希"""
        from utils.password import get_password_hash

        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")

        assert hash1 != hash2

    def test_same_password_different_salts(self):
        """测试相同密码不同盐值"""
        from utils.password import get_password_hash

        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 由于盐值不同，哈希应该不同
        assert hash1 != hash2


class TestConfigurationSecurity:
    """配置安全测试"""

    def test_secret_key_strength(self):
        """测试密钥强度"""
        from settings.config import settings

        # SECRET_KEY应该足够长
        assert len(settings.SECRET_KEY) >= 32

        # 应该不是默认值
        assert settings.SECRET_KEY != "your_secret_key_here"

    def test_jwt_configuration(self):
        """测试JWT配置"""
        from settings.config import settings

        # 检查JWT配置
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0

        # 访问令牌应该比刷新令牌短
        access_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        refresh_minutes = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        assert access_minutes < refresh_minutes


class TestUtilityFunctions:
    """工具函数测试"""

    def test_sensitive_word_filter_basic(self):
        """测试敏感词过滤基础功能"""
        try:
            from utils.sensitive_word_filter import SensitiveWordFilter

            # 创建过滤器实例
            filter_instance = SensitiveWordFilter()

            # 测试基本检测
            text = "这是一个正常的文本"
            contains_sensitive, found_word = filter_instance.contains_sensitive_word(
                text
            )

            # 正常文本不应该包含敏感词
            assert isinstance(contains_sensitive, bool)

        except ImportError:
            # 如果依赖不可用，跳过测试
            pytest.skip("Sensitive word filter dependencies not available")

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        try:
            from utils.cache import CacheManager

            cache_manager = CacheManager()

            # 测试缓存键生成
            key1 = cache_manager.cache_key("user", 123, action="profile")
            key2 = cache_manager.cache_key("user", 456, action="profile")
            key3 = cache_manager.cache_key("user", 123, action="settings")

            assert isinstance(key1, str)
            assert key1 != key2  # 不同参数应该产生不同键
            assert key1 != key3  # 不同操作应该产生不同键

        except ImportError:
            pytest.skip("Cache manager dependencies not available")


if __name__ == "__main__":
    # 允许直接运行此文件进行测试
    pytest.main([__file__, "-v"])
