import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import select
from backend.config import settings
from backend.models import LoginSession, User, KnowledgeBase, now

COOKIE = "auditor_session"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ":" + digest


def check_password(password: str, stored: str) -> bool:
    salt, digest = stored.split(":")
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(actual, digest)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def login_session(db, user_id: str, response):
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=token_hash(token), user_id=user_id, expires_at=now() + timedelta(days=7)))
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=settings().cookie_secure,
        max_age=7 * 86400,
        path="/",
    )


async def current_user(request: Request, db) -> User:
    token = request.cookies.get(COOKIE, "")
    if not token:
        raise HTTPException(401, "Sign in to continue.")
    user = await db.scalar(
        select(User)
        .join(LoginSession)
        .where(LoginSession.token_hash == token_hash(token), LoginSession.expires_at > now())
    )
    if not user:
        raise HTTPException(401, "Session expired. Sign in again.")
    return user


async def owned_kb(db, kb_id: str, user_id: str, lock=False):
    query = select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user_id)
    if lock:
        query = query.with_for_update()
    kb = await db.scalar(query)
    if not kb:
        raise HTTPException(404, "Knowledge base not found.")
    return kb


async def rate_limit(key: str, limit: int, seconds: int = 60):
    redis = Redis.from_url(settings().redis_url)
    try:
        script = "local n=redis.call('INCR',KEYS[1]);if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end;return n"
        count = await redis.eval(script, 1, "ratelimit:" + key, seconds)
        if count > limit:
            raise HTTPException(
                429, "Too many requests. Try again shortly.", headers={"Retry-After": str(seconds)}
            )
    finally:
        await redis.aclose()
