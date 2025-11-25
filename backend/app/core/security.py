from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from .config import get_settings


ALGORITHM = 'HS256'


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_delta = timedelta(minutes=expires_minutes or settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        'sub': subject,
        'exp': datetime.now(tz=timezone.utc) + expire_delta,
        'iat': datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError('Invalid token') from exc


