"""Unit tests for the cache helper utilities."""

from __future__ import annotations

import pytest

from utils import cache

pytestmark = pytest.mark.unit


class FakeCacheManager:
    """Minimal async cache backend used for testing the decorator."""

    def __init__(self):
        self.store: dict[str, object] = {}
        self.ttl: int | None = None

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        parts = [prefix]
        parts.extend(str(arg) for arg in args)
        if kwargs:
            parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(parts)

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value, ttl: int | None = None):
        applied_ttl = ttl or cache.settings.CACHE_TTL
        self.store[key] = value
        self.ttl = applied_ttl
        return True


def test_cache_key_orders_kwargs():
    manager = cache.CacheManager()

    key = manager.cache_key("user", 1, region="cn", level=3)

    assert key == "user:1:level:3:region:cn"


@pytest.mark.asyncio
async def test_cached_decorator_stores_and_reuses_results(monkeypatch):
    fake = FakeCacheManager()
    monkeypatch.setattr(cache, "cache_manager", fake)

    call_count = 0

    @cache.cached("expensive")
    async def expensive_call(arg):
        nonlocal call_count
        call_count += 1
        return {"value": arg}

    first = await expensive_call(5)
    second = await expensive_call(5)

    assert first == {"value": 5}
    assert second == {"value": 5}
    assert call_count == 1
    assert fake.store["expensive:5"] == {"value": 5}
    assert fake.ttl == cache.settings.CACHE_TTL


@pytest.mark.asyncio
async def test_cached_decorator_supports_custom_key_func(monkeypatch):
    fake = FakeCacheManager()
    monkeypatch.setattr(cache, "cache_manager", fake)

    @cache.cached("user", key_func=lambda user_id: f"user:{user_id}")
    async def load_user(user_id):
        return {"id": user_id}

    await load_user(99)

    assert fake.store["user:99"] == {"id": 99}
