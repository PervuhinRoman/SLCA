"""Application foundation; /health remains database-independent liveness."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.session import get_engine
from app.logging import configure_logging, logger, log_failure


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
