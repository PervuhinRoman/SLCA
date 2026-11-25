"""Login, logout and refresh endpoints (FR-11, FR-12, SEC-07)."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RefreshSession, User
from app.logging import log_failure, logger
from app.security import (
    NotAuthenticated,
    REFRESH_COOKIE,
    clear_auth_cookies,
    current_user,
    decode_token,
    get_db,
    resolve_user,
    revoke_refresh,
    set_auth_cookies,
    start_session,
    token_digest,
    verify_dummy,
    verify_password,
)
from app.templating import templates

router = APIRouter()


@router.get("/")
def index(user: User = Depends(current_user)) -> RedirectResponse:
    return RedirectResponse("/students", status_code=303)


@router.get("/login")
def login_form(request: Request, db: Session = Depends(get_db)):
    if resolve_user(request, db) is not None:
        return RedirectResponse("/students", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"current_user": None, "login": ""})


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    login_value = str(form.get("login", "")).strip()
    password = str(form.get("password", ""))

    user = db.scalar(select(User).where(User.login == login_value)) if login_value else None
    if user is None:
        verify_dummy(password)
        log_failure("login_failed", ValueError("unknown login"))
        return templates.TemplateResponse(
            request, "login.html",
            {"current_user": None, "login": login_value,
             "error": "Неверный логин или пароль."},
            status_code=401,
        )
    if not verify_password(password, user.password_hash):
        log_failure("login_failed", ValueError("wrong password"))
        return templates.TemplateResponse(
            request, "login.html",
            {"current_user": None, "login": login_value,
             "error": "Неверный логин или пароль."},
            status_code=401,
        )
    if not user.is_active:
        log_failure("login_failed", ValueError("inactive account"))
        return templates.TemplateResponse(
            request, "login.html",
            {"current_user": None, "login": login_value,
             "error": "Учётная запись заблокирована. Обратитесь к администратору."},
            status_code=403,
        )

    access, refresh = start_session(db, user)
    logger.info("login_success role=%s", user.role)
    response = RedirectResponse("/students", status_code=303)
    set_auth_cookies(response, access, refresh)
    return response


@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        return _login_redirect()
    try:
        payload = decode_token(token, "refresh")
        user_id = UUID(payload["sub"])
    except (NotAuthenticated, ValueError):
        return _login_redirect()

    session = db.scalar(
        select(RefreshSession).where(RefreshSession.token_digest == token_digest(token))
    )
    now = datetime.now(timezone.utc)
    user = db.get(User, user_id)
    if (session is None or session.revoked_at is not None
            or session.expires_at <= now or user is None or not user.is_active):
        return _login_redirect()

    session.revoked_at = now
    access, new_refresh = start_session(db, user)
    response = RedirectResponse("/students", status_code=303)
    set_auth_cookies(response, access, new_refresh)
    return response


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    revoke_refresh(db, request.cookies.get(REFRESH_COOKIE))
    response = RedirectResponse("/login", status_code=303)
    clear_auth_cookies(response)
    return response


def _login_redirect() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    clear_auth_cookies(response)
    return response
