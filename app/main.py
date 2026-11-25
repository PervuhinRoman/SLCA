"""StudentLedger web application: authentication, students and health."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import router as auth_router
from app.config import get_settings
from app.db.session import get_engine
from app.logging import configure_logging, logger, log_failure
from app.security import Forbidden, NotAuthenticated
from app.students import router as students_router
from app.templating import BASE_DIR, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info("configuration_loaded app_env=%s", settings.app_env)
    yield
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()


app = FastAPI(title="StudentLedger", docs_url=None, redoc_url=None,
              openapi_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(auth_router)
app.include_router(students_router)


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
async def forbidden_handler(request: Request, exc: Forbidden):
    return templates.TemplateResponse(request, "errors/403.html",
                                      {"current_user": None}, status_code=403)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(request, "errors/404.html",
                                          {"current_user": None}, status_code=404)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "Некорректные данные формы."})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.middleware("http")
async def safe_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except SQLAlchemyError as error:
        log_failure("database_operation_failed", error)
        return JSONResponse(status_code=503, content={
            "detail": "Операция с БД недоступна. Повторите позже или обратитесь к администратору."
        })
    except Exception as error:
        log_failure("request_failed", error)
        return JSONResponse(status_code=500, content={
            "detail": "Не удалось выполнить операцию. Обратитесь к администратору."
        })


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness, not database readiness."""
    return {"status": "ok"}
