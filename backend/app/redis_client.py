from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

import redis

from app.config import settings

_pool: Optional[redis.ConnectionPool] = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
    return redis.Redis(connection_pool=_pool)


def _today_utc_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def budget_key(day: Optional[str] = None) -> str:
    return f"bricklink:budget:{day or _today_utc_key()}"


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((tomorrow - now).total_seconds()), 1)


class BudgetExhaustedError(Exception):
    pass


def get_budget_used() -> int:
    r = get_redis()
    val = r.get(budget_key())
    return int(val) if val is not None else 0


def get_budget_remaining(cap: int) -> int:
    return max(cap - get_budget_used(), 0)


def consume_budget(cap: int, n: int = 1) -> int:
    r = get_redis()
    key = budget_key()
    pipe = r.pipeline()
    pipe.incrby(key, n)
    pipe.expire(key, _seconds_until_utc_midnight(), nx=True)
    used, _ = pipe.execute()
    used = int(used)
    if used > cap:
        r.decrby(key, n)
        raise BudgetExhaustedError(f"BrickLink daily budget exhausted ({cap}/{cap})")
    return used
