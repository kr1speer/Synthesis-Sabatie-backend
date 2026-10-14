import os
import uuid

import redis

SABATIER_REDIS_HOST = os.getenv("SABATIER_REDIS_HOST", "localhost")
SABATIER_REDIS_PORT = int(os.getenv("SABATIER_REDIS_PORT", "6379"))

SESSION_COOKIE_NAME = "session_id"
SESSION_TTL_SECONDS = 24 * 60 * 60

SESSION_KEY_PREFIX = "session:"

redis_client = redis.Redis(
    host=SABATIER_REDIS_HOST,
    port=SABATIER_REDIS_PORT,
    decode_responses=True,
)


def session_key(session_id: str) -> str:
    return f"{SESSION_KEY_PREFIX}{session_id}"


def create_session(chemist_id: int, chemist_login: str, is_moderator: bool) -> str:
    session_id = uuid.uuid4().hex

    redis_client.hset(
        session_key(session_id),
        mapping={
            "chemist_id": chemist_id,
            "chemist_login": chemist_login,
            "is_moderator": int(is_moderator),
        },
    )
    redis_client.expire(session_key(session_id), SESSION_TTL_SECONDS)
    return session_id


def get_session_chemist_id(session_id: str) -> int | None:
    chemist_id = redis_client.hget(session_key(session_id), "chemist_id")
    return int(chemist_id) if chemist_id is not None else None


def delete_session(session_id: str) -> None:
    redis_client.delete(session_key(session_id))
