"""Password hashing, JWT issuing and request authentication dependencies."""
from collections.abc import Callable, Iterator
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid4

from fastapi import Depends, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import RefreshSession, User
from app.db.session import transaction

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
ALGORITHM = "HS256"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# A fixed hash used to keep failed-login timing similar for unknown logins.
_DUMMY_HASH = "$2b$12$C6UzMDM.H6dfI/f/IKcEeO7Z0n8e0lJ0a3oXbG1pVn8mQ0hK5o4W2"


class NotAuthenticated(Exception):
    """No valid access token: the browser is sent to the login page."""


class Forbidden(Exception):
    """Authenticated user tries an operation outside the role permissions."""


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_context.verify(password, password_hash)
    except ValueError:
        return False


def verify_dummy(password: str) -> None:
    password_context.verify(password, _DUMMY_HASH)


def _secret() -> str:
    return get_settings().require_jwt_secret()


def _encode(user: User, token_type: str, lifetime: timedelta, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def create_access_token(user: User) -> str:
    settings = get_settings()
    return _encode(user, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user: User) -> str:
    settings = get_settings()
    return _encode(user, "refresh", timedelta(days=settings.refresh_token_days), jti=str(uuid4()))


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except JWTError as error:
        raise NotAuthenticated from error
    if payload.get("type") != expected_type or not isinstance(payload.get("sub"), str):
        raise NotAuthenticated
    if "exp" not in payload:
        raise NotAuthenticated
    return payload


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def start_session(db: Session, user: User) -> tuple[str, str]:
    """Issue a token pair and remember the refresh digest (never the token)."""
    settings = get_settings()
    access = create_access_token(user)
    refresh = create_refresh_token(user)
    db.add(RefreshSession(
        user_id=user.id,
        token_digest=token_digest(refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    ))
    db.flush()
    return access, refresh


def set_auth_cookies(response, access: str, refresh: str) -> None:
    settings = get_settings()
    response.set_cookie(
        ACCESS_COOKIE, access, max_age=settings.access_token_minutes * 60,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh, max_age=settings.refresh_token_days * 86400,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )


def clear_auth_cookies(response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def get_db() -> Iterator[Session]:
    with transaction() as session:
        yield session


def resolve_user(request: Request, db: Session) -> User | None:
    """Return the active user for a valid access cookie, otherwise None."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return None
    try:
        payload = decode_token(token, "access")
        user_id = UUID(payload["sub"])
    except (NotAuthenticated, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = resolve_user(request, db)
    if user is None:
        raise NotAuthenticated
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise Forbidden
        return user

    return dependency


def revoke_refresh(db: Session, token: str | None) -> None:
    if not token:
        return
    session = db.scalar(
        select(RefreshSession).where(RefreshSession.token_digest == token_digest(token))
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.flush()
