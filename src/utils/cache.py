import asyncio
import json
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis.asyncio as redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from log import logger
from schemas.base import Fail, Success, SuccessExtra
from settings.config import settings

# 空值哨兵：标记"已查询过且确认不存在"的 key，防止穿透
_NULL_SENTINEL = "__cache_null__"
_NULL_TTL = 60  # 空值缓存只保留 60s，避免长期错误

# Redis 重连节流：失败后至少等待这么久才重试 connect
_RECONNECT_INTERVAL = 5.0


class CacheManager:
    """Redis 缓存管理器（带重连、防穿透、防雪崩）"""

    def __init__(self):
        self.redis: redis.Redis | None = None
        self._loop_id: int | None = None
        self._last_reconnect_at: float = 0.0
        self._reconnect_lock = asyncio.Lock()

    async def connect(self) -> None:
        """初始化 Redis 连接（lifespan 启动时调用一次）"""
        if self.redis is not None and self._is_current_loop_connection():
            return
        await self._try_connect()

    def _is_current_loop_connection(self) -> bool:
        try:
            return self._loop_id == id(asyncio.get_running_loop())
        except RuntimeError:
            return False

    async def _drop_connection(self, reason: str) -> None:
        client = self.redis
        self.redis = None
        self._loop_id = None
        self._last_reconnect_at = 0.0
        if client is None:
            return
        try:
            close = getattr(client, "aclose", None) or client.close
            await close()
        except Exception as e:
            logger.debug(f"Redis 连接丢弃时关闭失败 reason={reason}: {e}")

    async def _try_connect(self) -> bool:
        """尝试建立连接。成功返回 True；失败 self.redis 保持 None。

        广义捕获 Exception：含 RuntimeError("Event loop is closed")
        等跨 fixture / event-loop 复用场景的非 Redis 异常。
        """
        async with self._reconnect_lock:
            if self.redis is not None and self._is_current_loop_connection():
                return True
            if self.redis is not None:
                await self._drop_connection("event-loop changed")
            now = time.monotonic()
            if now - self._last_reconnect_at < _RECONNECT_INTERVAL:
                return False
            self._last_reconnect_at = now
            client = None
            try:
                client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    health_check_interval=30,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                await client.ping()
                self.redis = client
                self._loop_id = id(asyncio.get_running_loop())
                logger.info("Redis 连接成功")
                return True
            except Exception as e:
                logger.warning(f"Redis 不可用，缓存降级：{e}")
                self.redis = None
                self._loop_id = None
                if client is not None:
                    try:
                        close = getattr(client, "aclose", None) or client.close
                        await close()
                    except Exception:
                        pass
                return False

    async def _ensure_connected(self) -> bool:
        """供读写方法按需重连。已连接直接返回；否则尝试一次（受节流）"""
        if self.redis is not None and self._is_current_loop_connection():
            return True
        if self.redis is not None:
            await self._drop_connection("event-loop changed")
        return await self._try_connect()

    async def disconnect(self) -> None:
        if self.redis is not None:
            try:
                await self.redis.close()
            except Exception as e:
                logger.warning(f"Redis 关闭异常：{e}")
            finally:
                self.redis = None
                self._loop_id = None
                logger.info("Redis 连接已断开")

    async def get(self, key: str) -> Any | None:
        if not await self._ensure_connected():
            return None
        try:
            data = await self.redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except (RedisConnectionError, RedisTimeoutError, OSError, RuntimeError) as e:
            logger.warning(f"Redis 读取失败，标记重连 key={key}: {e}")
            await self._drop_connection("read failed")
            return None
        except RedisError as e:
            logger.error(f"获取缓存失败 key={key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        if not await self._ensure_connected():
            return False
        try:
            base_ttl = ttl if ttl is not None else settings.CACHE_TTL
            jitter = random.randint(0, max(1, base_ttl // 10))  # 抖动 ≤10%
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis.setex(key, base_ttl + jitter, serialized)
            return True
        except (RedisConnectionError, RedisTimeoutError, OSError, RuntimeError) as e:
            logger.warning(f"Redis 写入失败，标记重连 key={key}: {e}")
            await self._drop_connection("write failed")
            return False
        except RedisError as e:
            logger.error(f"设置缓存失败 key={key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not await self._ensure_connected():
            return False
        try:
            return bool(await self.redis.delete(key))
        except (RedisConnectionError, RedisTimeoutError, OSError, RuntimeError) as e:
            logger.warning(f"Redis 删除失败，标记重连 key={key}: {e}")
            await self._drop_connection("delete failed")
            return False
        except RedisError as e:
            logger.error(f"删除缓存失败 key={key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        if not await self._ensure_connected():
            return False
        try:
            return bool(await self.redis.exists(key))
        except (RedisConnectionError, RedisTimeoutError, OSError, RuntimeError) as e:
            logger.warning(f"Redis exists 失败，标记重连 key={key}: {e}")
            await self._drop_connection("exists failed")
            return False
        except RedisError as e:
            logger.error(f"检查缓存存在性失败 key={key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        if not await self._ensure_connected():
            return 0
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except (RedisConnectionError, RedisTimeoutError, OSError, RuntimeError) as e:
            logger.warning(f"Redis 批量删除失败，标记重连 pattern={pattern}: {e}")
            await self._drop_connection("clear_pattern failed")
            return 0
        except RedisError as e:
            logger.error(f"批量删除缓存失败 pattern={pattern}: {e}")
            return 0

    @property
    def is_available(self) -> bool:
        """供 metrics / 健康检查使用，不触发重连"""
        return self.redis is not None

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        key_parts = [prefix]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
        return ":".join(key_parts)


cache_manager = CacheManager()


def cached(prefix: str, ttl: int | None = None, key_func: Callable | None = None):
    """缓存装饰器

    防穿透：原函数返回 None 时，写入 60s 短 TTL 的空值哨兵，避免重复打 DB。
    防雪崩：set 时 TTL 自带抖动（在 CacheManager.set 中实现）。
    Redis 不可用时：直接执行原函数，不缓存，不阻断业务。
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = (
                key_func(*args, **kwargs)
                if key_func
                else cache_manager.cache_key(prefix, *args, **kwargs)
            )

            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                # 空值哨兵命中
                if cached_result == _NULL_SENTINEL:
                    logger.debug(f"缓存命中(空值): {cache_key}")
                    return None
                # Response 对象重建
                if isinstance(cached_result, dict) and cached_result.get(
                    "__response__"
                ):
                    response_type = cached_result.get("class")
                    payload = cached_result.get("payload", {})
                    response_cls = {
                        "Success": Success,
                        "Fail": Fail,
                        "SuccessExtra": SuccessExtra,
                    }.get(response_type, Success)
                    return response_cls(**payload)
                logger.debug(f"缓存命中: {cache_key}")
                return cached_result

            result = await func(*args, **kwargs)

            # 防穿透：None 也缓存（短 TTL 哨兵）
            if result is None:
                await cache_manager.set(cache_key, _NULL_SENTINEL, _NULL_TTL)
                return None

            value_to_cache: Any = result
            if isinstance(result, Success | Fail | SuccessExtra):
                body_bytes = result.body
                if isinstance(body_bytes, bytes):
                    payload = json.loads(body_bytes.decode("utf-8"))
                else:
                    payload = json.loads(body_bytes)
                value_to_cache = {
                    "__response__": True,
                    "class": result.__class__.__name__,
                    "payload": payload,
                }
            await cache_manager.set(cache_key, value_to_cache, ttl)
            logger.debug(f"缓存设置: {cache_key}")
            return result

        return wrapper

    return decorator


async def clear_user_cache(user_id: int) -> int:
    patterns = [
        f"user:{user_id}:*",
        f"userinfo:{user_id}",
        f"user_roles:{user_id}",
        f"user_permissions:{user_id}",
        f"user_perms:{user_id}",
    ]
    total = 0
    for pattern in patterns:
        total += await cache_manager.clear_pattern(pattern)
    logger.info(f"清除用户 {user_id} 相关缓存，共 {total} 个键")
    return total


async def clear_role_cache(role_id: int) -> int:
    patterns = [
        f"role:{role_id}:*",
        f"role_permissions:{role_id}",
        f"role_menus:{role_id}",
    ]
    total = 0
    for pattern in patterns:
        total += await cache_manager.clear_pattern(pattern)
    logger.info(f"清除角色 {role_id} 相关缓存，共 {total} 个键")
    return total


async def clear_user_perms_cache_all() -> int:
    """清除所有用户的权限缓存（角色权限变更时使用）"""
    total = await cache_manager.clear_pattern("user_perms:*")
    logger.info(f"清除全部用户权限缓存，共 {total} 个键")
    return total
