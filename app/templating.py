"""Shared Jinja2 environment and template helpers."""
from pathlib import Path

from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["role_labels"] = {
    "administrator": "администратор",
    "teacher": "преподаватель",
    "student": "студент",
}
templates.env.globals["education_forms"] = ("очная", "очно-заочная", "заочная")
