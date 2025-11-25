import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import LoginCode, User


CODE_TTL_MINUTES = 10


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def generate_code() -> str:
    return f'{secrets.randbelow(1_000_000):06d}'


async def upsert_user(session: AsyncSession, email: str, full_name: str | None) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user:
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            await session.flush()
        return user

    user = User(email=email, full_name=full_name)
    session.add(user)
    await session.flush()
    return user


async def store_code(session: AsyncSession, user: User, code: str) -> LoginCode:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES)
    code_entity = LoginCode(user_id=user.id, code_hash=_hash_code(code), expires_at=expires_at)
    session.add(code_entity)
    await session.flush()
    return code_entity


async def verify_code(session: AsyncSession, email: str, code: str) -> User | None:
    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        return None

    code_hash = _hash_code(code)
    stmt = (
        select(LoginCode)
        .where(
            LoginCode.user_id == user.id,
            LoginCode.code_hash == code_hash,
            LoginCode.consumed_at.is_(None),
            LoginCode.expires_at > datetime.now(tz=timezone.utc),
        )
        .order_by(LoginCode.created_at.desc())
    )
    login_code = await session.scalar(stmt)
    if not login_code:
        return None

    await session.execute(
        update(LoginCode)
        .where(LoginCode.id == login_code.id)
        .values(consumed_at=datetime.now(tz=timezone.utc))
    )
    user.last_login_at = datetime.now(tz=timezone.utc)
    await session.flush()
    return user


