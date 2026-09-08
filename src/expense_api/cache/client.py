from redis.asyncio import Redis

from expense_api.core.config import Settings


def create_redis_client(settings: Settings) -> Redis:
    """Create the shared asynchronous Redis client for this process."""
    return Redis.from_url(
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        health_check_interval=settings.redis_health_check_interval_seconds,
    )
