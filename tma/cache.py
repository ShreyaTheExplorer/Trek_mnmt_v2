import json
import fnmatch
import time
import logging
from typing import Any, Optional
import redis
from flask import jsonify, current_app

logger = logging.getLogger(__name__)

_redis_client = None
_redis_checked = False
_redis_available = False

# Fallback store when Redis is temporarily offline (stores {key: (json_str, expire_timestamp)})
_memory_cache = {}

def get_redis_client():
    """
    Get or initialize the redis-py client.
    Tests connection once and caches availability status.
    """
    global _redis_client, _redis_checked, _redis_available

    if _redis_client is not None and _redis_available:
        return _redis_client

    try:
        from config import Config
        redis_url = Config.REDIS_URL
        if current_app:
            redis_url = current_app.config.get('REDIS_URL', redis_url)

        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3
        )
        client.ping()
        _redis_client = client
        _redis_available = True
        _redis_checked = True
        return _redis_client
    except (redis.RedisError, Exception) as e:
        if not _redis_checked or _redis_available:
            logger.warning(f"[Cache Notice] Redis server at {redis_url if 'redis_url' in locals() else 'default'} is offline ({e}). Gracefully utilizing fallback cache.")
        _redis_available = False
        _redis_checked = True
        return None


def get_json(key: str) -> Optional[Any]:
    """
    Fetch and deserialize JSON from Redis by key.
    Fails gracefully if Redis is down (falls back to memory store, logs warning).
    """
    # 1. Try Redis
    r = get_redis_client()
    if r:
        try:
            val = r.get(key)
            if val is not None:
                return json.loads(val)
            return None
        except (redis.RedisError, Exception) as e:
            logger.warning(f"[Cache Warning] Redis get_json failed for '{key}': {e}. Using fallback.")

    # 2. Graceful fallback
    item = _memory_cache.get(key)
    if item:
        data_str, expire_at = item
        if time.time() < expire_at:
            return json.loads(data_str)
        else:
            # Expired
            _memory_cache.pop(key, None)
    return None


def set_json(key: str, value: Any, ttl: int = 180) -> bool:
    """
    Serialize value to JSON and store with an expiration (TTL 60-300 s).
    Fails gracefully if Redis is down.
    """
    payload_str = json.dumps(value)

    # 1. Try Redis
    r = get_redis_client()
    if r:
        try:
            r.set(key, payload_str, ex=ttl)
            return True
        except (redis.RedisError, Exception) as e:
            logger.warning(f"[Cache Warning] Redis set_json failed for '{key}': {e}. Storing in fallback cache.")

    # 2. Graceful fallback
    _memory_cache[key] = (payload_str, time.time() + ttl)
    return True


def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob pattern (e.g. 'treks:user:*').
    Fails gracefully if Redis is down.
    """
    deleted_count = 0

    # 1. Try Redis
    r = get_redis_client()
    if r:
        try:
            keys = r.keys(pattern)
            if keys:
                deleted_count = r.delete(*keys)
        except (redis.RedisError, Exception) as e:
            logger.warning(f"[Cache Warning] Redis delete_pattern failed for '{pattern}': {e}.")

    # 2. Clear matching keys from fallback memory cache
    matched_fallback = [k for k in _memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
    for k in matched_fallback:
        _memory_cache.pop(k, None)
        deleted_count += 1

    return deleted_count


def invalidate_trek_cache(trek_id: Optional[int] = None) -> None:
    """
    Cache invalidation hook:
    Clears all cached user trek listings, trek details, admin dashboard, and stats.
    Called whenever a trek, slots, status, or booking changes.
    """
    try:
        # Invalidate user trek catalog listings
        delete_pattern("treks:user:*")
        # Invalidate specific trek and general trek details
        if trek_id is not None:
            delete_pattern(f"trek:detail:{trek_id}")
        delete_pattern("trek:detail:*")
        # Invalidate admin dashboard and stats cache
        delete_pattern("admin:dashboard*")
        delete_pattern("admin:stats*")
    except Exception as e:
        logger.warning(f"[Cache Warning] invalidate_trek_cache encountered an issue: {e}")


def cache_response(payload: dict, cache_hit: bool, status_code: int = 200):
    """
    Response helper injecting the X-Cache: HIT / MISS header.
    Demonstrates whether the response was served from cache or database.
    """
    response = jsonify(payload)
    response.headers['X-Cache'] = 'HIT' if cache_hit else 'MISS'
    return response, status_code
