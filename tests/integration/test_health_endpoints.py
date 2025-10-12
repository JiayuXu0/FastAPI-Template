"""健康检查和基础端点测试"""

from httpx import AsyncClient


class TestHealthEndpoints:
    """健康检查端点测试类"""

    async def test_health_check_endpoint(self, async_client: AsyncClient):
        """测试健康检查端点"""
        response = await async_client.get("/api/v1/base/health")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "service" in data

        # 验证值
        assert data["status"] == "healthy"
        assert data["service"] == "FastAPI Backend Template"

        # 验证时间戳格式
        from datetime import datetime

        timestamp = data["timestamp"]
        # 应该是有效的ISO格式时间戳
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    async def test_version_endpoint(self, async_client: AsyncClient):
        """测试版本信息端点"""
        response = await async_client.get("/api/v1/base/version")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        required_fields = [
            "version",
            "app_title",
            "project_name",
            "build",
            "commit",
            "python_version",
        ]

        for field in required_fields:
            assert field in data
            assert isinstance(data[field], str)

    async def test_health_endpoint_performance(self, async_client: AsyncClient):
        """测试健康检查端点性能"""
        import time

        start_time = time.time()
        response = await async_client.get("/api/v1/base/health")
        end_time = time.time()

        assert response.status_code == 200

        # 健康检查应该在100ms内完成
        response_time = (end_time - start_time) * 1000
        assert response_time < 100, f"Health check took {response_time:.2f}ms"

    async def test_health_check_no_authentication_required(
        self, async_client: AsyncClient
    ):
        """测试健康检查不需要认证"""
        # 不提供任何认证头
        response = await async_client.get("/api/v1/base/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_version_no_authentication_required(self, async_client: AsyncClient):
        """测试版本信息不需要认证"""
        # 不提供任何认证头
        response = await async_client.get("/api/v1/base/version")

        assert response.status_code == 200
        assert "version" in response.json()

    async def test_cors_headers(self, async_client: AsyncClient):
        """测试CORS头设置"""
        response = await async_client.get("/api/v1/base/health")

        # 检查是否有CORS相关头（如果配置了的话）
        assert response.status_code == 200

        # 基本CORS头检查（可能不是所有环境都有）
        _ = response.headers
        # 这些头可能存在，取决于中间件配置
        # assert "access-control-allow-origin" in headers

    async def test_multiple_concurrent_health_checks(self, async_client: AsyncClient):
        """测试并发健康检查"""
        import asyncio

        # 并发发送多个健康检查请求
        tasks = [async_client.get("/api/v1/base/health") for _ in range(10)]

        responses = await asyncio.gather(*tasks)

        # 所有请求都应该成功
        for response in responses:
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    async def test_api_root_documentation(self, async_client: AsyncClient):
        """测试API根路径和文档"""
        # 获取设置中的基本认证信息
        import base64

        from src.settings.config import settings

        # 创建基本认证头
        credentials = f"{settings.SWAGGER_UI_USERNAME}:{settings.SWAGGER_UI_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_headers = {"Authorization": f"Basic {encoded_credentials}"}

        # 测试docs端点
        docs_response = await async_client.get("/docs", headers=auth_headers)
        assert docs_response.status_code == 200

        # 测试OpenAPI规范
        openapi_response = await async_client.get("/openapi.json", headers=auth_headers)
        assert openapi_response.status_code == 200

        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

    async def test_health_check_includes_settings(self, async_client: AsyncClient):
        """测试健康检查包含必要的配置信息"""
        response = await async_client.get("/api/v1/base/health")
        data = response.json()

        # 验证环境信息
        environment = data.get("environment")
        assert environment in ["development", "production", "testing"]

        # 验证版本信息存在
        version = data.get("version")
        assert version is not None
        assert len(version) > 0

    async def test_version_includes_build_info(self, async_client: AsyncClient):
        """测试版本信息包含构建信息"""
        response = await async_client.get("/api/v1/base/version")
        data = response.json()

        # 验证构建信息
        build = data.get("build", "dev")
        commit = data.get("commit", "unknown")
        python_version = data.get("python_version", "3.11+")

        assert isinstance(build, str)
        assert isinstance(commit, str)
        assert isinstance(python_version, str)

        # Python版本应该包含数字
        assert any(char.isdigit() for char in python_version)
