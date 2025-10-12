"""测试配置和固件"""

import asyncio
import os
import subprocess
import sys
import tempfile
import warnings
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SWAGGER_UI_PASSWORD", "test_password")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("APP_TITLE", "FastAPI Backend Template")
os.environ.setdefault("PROJECT_NAME", "FastAPI Backend Template")

try:  # pragma: no cover - fallback for environments without pytest-asyncio
    import pytest_asyncio  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-asyncio>=0.23,<0.24"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        warnings.warn(
            "Installed pytest-asyncio dynamically to enable async fixtures."
        )
        import pytest_asyncio  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover
        warnings.warn(
            f"pytest-asyncio is required for async tests but could not be installed: {exc}"
        )

try:  # pragma: no cover - ensure pytest-cov is available for coverage reporting
    import pytest_cov  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytest-cov>=4.1"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        warnings.warn("Installed pytest-cov dynamically to enable coverage reporting.")
        import pytest_cov  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover
        warnings.warn(
            f"pytest-cov is required for coverage reporting but could not be installed: {exc}"
        )

loaded_plugins = []
if "pytest_asyncio" in sys.modules:
    loaded_plugins.append("pytest_asyncio")
if "pytest_cov" in sys.modules:
    loaded_plugins.append("pytest_cov")

if loaded_plugins:  # pragma: no cover - plugin auto-registration helper
    pytest_plugins = tuple(loaded_plugins)

from src import app
from tortoise import Tortoise


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    # 设置测试环境变量
    import os

    os.environ["TESTING"] = "true"

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    # 使用临时SQLite数据库
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    db_url = f"sqlite://{temp_db.name}"

    # 初始化Tortoise ORM
    test_config = {
        "connections": {"default": db_url},
        "apps": {
            "models": {
                "models": ["models", "aerich.models"],
                "default_connection": "default",
            }
        },
        "use_tz": False,
        "timezone": "Asia/Shanghai",
    }

    await Tortoise.init(config=test_config)

    # 生成数据库架构
    await Tortoise.generate_schemas()

    yield

    # 清理
    await Tortoise.close_connections()
    os.unlink(temp_db.name)


@pytest.fixture
def client():
    """同步测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def clean_database():
    """清理数据库"""
    from src.models.admin import Api, AuditLog, Dept, FileMapping, Menu, Role, User

    try:
        # 清理所有测试数据（忽略外键约束错误）
        await User.all().delete()
        await Role.all().delete()
        await Api.all().delete()
        await Menu.all().delete()
        await Dept.all().delete()
        await AuditLog.all().delete()
        await FileMapping.all().delete()
    except Exception:
        # 如果删除失败，可能是数据库未初始化，直接跳过
        pass


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端"""
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def admin_token(async_client: AsyncClient, clean_database) -> str:
    """获取管理员Token"""
    import os
    import uuid

    from src.repositories.user import user_repository
    from src.schemas.users import UserCreate

    # 确保测试环境变量设置
    os.environ["TESTING"] = "true"

    # 使用随机用户名避免冲突
    unique_id = str(uuid.uuid4())[:8]
    admin_user = UserCreate(
        username=f"admin_{unique_id}",
        email=f"admin_{unique_id}@test.com",
        password="Test123456",
        is_superuser=True,
        is_active=True,
    )

    try:
        await user_repository.create_user(obj_in=admin_user)
    except Exception as e:
        print(f"创建用户失败: {e}")
        raise

    # 登录获取token，加重试机制
    import time

    for attempt in range(5):  # 增加重试次数
        try:
            response = await async_client.post(
                "/api/v1/base/access_token",
                json={"username": f"admin_{unique_id}", "password": "Test123456"},
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("data", {}).get("access_token")
                if token:
                    return token
                else:
                    print(f"响应数据中没有token: {data}")
                    raise Exception("Token not found in response")
            elif response.status_code == 429:  # 限流
                print(f"遇到限流，等待后重试 (尝试 {attempt + 1}/5)")
                time.sleep(2)
                continue
            else:
                print(f"登录失败: {response.status_code} - {response.text}")
                if attempt < 4:  # 不是最后一次尝试
                    time.sleep(1)
                    continue
                raise Exception(f"登录失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"登录尝试 {attempt + 1} 失败: {e}")
            if attempt == 4:  # 最后一次尝试
                raise e
            time.sleep(1)

    raise Exception("所有登录尝试都失败了")


@pytest.fixture
async def normal_user_token(async_client: AsyncClient, clean_database) -> str:
    """获取普通用户Token"""
    import os
    import uuid

    from src.repositories.user import user_repository
    from src.schemas.users import UserCreate

    # 确保测试环境变量设置
    os.environ["TESTING"] = "true"

    # 使用随机用户名避免冲突
    unique_id = str(uuid.uuid4())[:8]
    normal_user = UserCreate(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@test.com",
        password="Test123456",
        is_superuser=False,
        is_active=True,
    )

    try:
        await user_repository.create_user(obj_in=normal_user)
    except Exception as e:
        print(f"创建普通用户失败: {e}")
        raise

    # 登录获取token，加重试机制
    import time

    for attempt in range(5):
        try:
            response = await async_client.post(
                "/api/v1/base/access_token",
                json={"username": f"user_{unique_id}", "password": "Test123456"},
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("data", {}).get("access_token")
                if token:
                    return token
                else:
                    print(f"普通用户响应数据中没有token: {data}")
                    raise Exception("Token not found in response")
            elif response.status_code == 429:  # 限流
                print(f"普通用户遇到限流，等待后重试 (尝试 {attempt + 1}/5)")
                time.sleep(2)
                continue
            else:
                print(f"普通用户登录失败: {response.status_code} - {response.text}")
                if attempt < 4:  # 不是最后一次尝试
                    time.sleep(1)
                    continue
                raise Exception(
                    f"普通用户登录失败: {response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"普通用户登录尝试 {attempt + 1} 失败: {e}")
            if attempt == 4:  # 最后一次尝试
                raise e
            time.sleep(1)

    raise Exception("所有普通用户登录尝试都失败了")


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    """认证头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def normal_auth_headers(normal_user_token: str) -> dict:
    """普通用户认证头"""
    return {"Authorization": f"Bearer {normal_user_token}"}
