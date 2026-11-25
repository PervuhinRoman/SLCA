"""Allowlisted diagnostics: no exception messages, SQL, request data or DSNs."""
import logging
import re

logger = logging.getLogger("studentledger")


def configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_failure(event: str, error: Exception) -> None:
    state = getattr(getattr(error, "orig", None), "sqlstate", None)
    state = state if isinstance(state, str) and re.fullmatch(r"[0-9A-Z]{5}", state) else "unavailable"
    logger.error("%s error_type=%s sqlstate=%s", event, type(error).__name__, state)
