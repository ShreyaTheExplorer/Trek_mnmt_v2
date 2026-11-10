import redis
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

_redis_client = None

def get_redis_client(app=None):
    """
    Returns a singleton Redis client using the configured REDIS_URL.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if app is not None:
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    else:
        from flask import current_app
        redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')

    _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    return _redis_client
