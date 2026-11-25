"""Student list and creation (FR-01, FR-02, SEC-09, SEC-10, UI-01–UI-04)."""
import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Student, User
from app.security import get_db, hash_password, require_roles
from app.templating import templates

router = APIRouter()

LOGIN_RE = re.compile(r"^[A-Za-z0-9._-]{3,128}$")


def _values(form) -> dict[str, str]:
    return {
        "last_name": str(form.get("last_name", "")).strip(),
        "first_name": str(form.get("first_name", "")).strip(),
        "patronymic": str(form.get("patronymic", "")).strip(),
        "admission_year": str(form.get("admission_year", "")).strip(),
        "education_form": str(form.get("education_form", "")).strip(),
        "group_name": str(form.get("group_name", "")).strip(),
        "login": str(form.get("login", "")).strip(),
        "password": str(form.get("password", "")),
    }


def validate(values: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not values["last_name"]:
        errors["last_name"] = "Укажите фамилию."
    elif len(values["last_name"]) > 100:
        errors["last_name"] = "Фамилия: не более 100 символов."
    if not values["first_name"]:
        errors["first_name"] = "Укажите имя."
    elif len(values["first_name"]) > 100:
        errors["first_name"] = "Имя: не более 100 символов."
    if len(values["patronymic"]) > 100:
        errors["patronymic"] = "Отчество: не более 100 символов."

    year = values["admission_year"]
    if not re.fullmatch(r"\d{4}", year):
        errors["admission_year"] = "Год поступления: четыре цифры, например 2024."
    elif not 1900 <= int(year) <= 2100:
        errors["admission_year"] = "Год поступления: от 1900 до 2100."

    if values["education_form"] not in ("очная", "очно-заочная", "заочная"):
        errors["education_form"] = "Выберите форму обучения из списка."
    if not values["group_name"]:
        errors["group_name"] = "Укажите группу."
    elif len(values["group_name"]) > 64:
        errors["group_name"] = "Группа: не более 64 символов."

    if not LOGIN_RE.fullmatch(values["login"]):
        errors["login"] = ("Логин: от 3 до 128 символов, латинские буквы, цифры, "
                           "точка, дефис или подчёркивание.")
    if not 8 <= len(values["password"]) <= 128:
        errors["password"] = "Пароль: от 8 до 128 символов."
    return errors


@router.get("/students")
def students_list(request: Request, user: User = Depends(require_roles(
        "administrator", "teacher", "student")), db: Session = Depends(get_db)):
    if user.role == "student":
        rows = db.scalars(select(Student).where(Student.user_id == user.id)).all()
    else:
        rows = db.scalars(
            select(Student).order_by(Student.last_name, Student.first_name)
        ).all()
    return templates.TemplateResponse(request, "students/list.html", {
        "current_user": user,
        "students": rows,
        "created": request.query_params.get("created") == "1",
    })


@router.get("/students/new")
def student_form(request: Request, user: User = Depends(require_roles("administrator"))):
    return templates.TemplateResponse(request, "students/new.html", {
        "current_user": user,
        "values": {},
        "errors": {},
    })


@router.post("/students/new")
async def student_create(request: Request,
                         user: User = Depends(require_roles("administrator")),
                         db: Session = Depends(get_db)):
    values = _values(await request.form())
    errors = validate(values)
    if not errors:
        login_taken = db.scalar(select(User.id).where(User.login == values["login"]))
        if login_taken is not None:
            errors["login"] = "Логин уже занят."
    if errors:
        values["password"] = ""
        return templates.TemplateResponse(request, "students/new.html", {
            "current_user": user,
            "values": values,
            "errors": errors,
        }, status_code=400)

    try:
        with db.begin_nested():
            account = User(login=values["login"],
                           password_hash=hash_password(values["password"]),
                           role="student")
            db.add(account)
            db.flush()
            student = Student(
                user_id=account.id,
                last_name=values["last_name"],
                first_name=values["first_name"],
                patronymic=values["patronymic"] or None,
                admission_year=int(values["admission_year"]),
                education_form=values["education_form"],
                group_name=values["group_name"],
            )
            db.add(student)
            db.flush()
            db.add(AuditLog(user_id=user.id, operation="student.create",
                            object_type="student", object_id=student.id,
                            result="success"))
            db.flush()
    except IntegrityError:
        values["password"] = ""
        return templates.TemplateResponse(request, "students/new.html", {
            "current_user": user,
            "values": values,
            "errors": {"login": "Логин уже занят."},
        }, status_code=400)

    return RedirectResponse("/students?created=1", status_code=303)
