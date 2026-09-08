"""Redis-backed cache infrastructure."""

from expense_api.cache.client import create_redis_client

__all__ = ["create_redis_client"]
