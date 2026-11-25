"""APP-02/APP-03/APP-04: authentication, students, RBAC and audit."""
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.db.models import AuditLog, RefreshSession, Student, User
from app.db.session import transaction
from app.security import hash_password, token_digest

pytestmark = pytest.mark.integration

PASSWORD = "student-pass-1"
ADMIN_PASSWORD = "admin-pass-1"

STUDENT_FORM = {
    "last_name": "Иванов",
    "first_name": "Иван",
    "patronymic": "Иванович",
    "admission_year": "2024",
    "education_form": "очная",
    "group_name": "241-3211",
    "login": "ivanov",
    "password": "ivanov-pass-1",
}


def add_user(database, login, role, password=PASSWORD, active=True):
    with transaction(database) as session:
        user = User(login=login, password_hash=hash_password(password),
                    role=role, is_active=active)
        session.add(user)
        session.flush()
        return user.id


def add_student(database, user_id, last_name, login):
    with transaction(database) as session:
        session.add(Student(user_id=user_id, last_name=last_name, first_name="Тест",
                            admission_year=2025, education_form="очная",
                            group_name="TEST-1"))


def login(client, login_value, password=PASSWORD):
    return client.post("/login", data={"login": login_value, "password": password},
                       follow_redirects=False)


@pytest.fixture
def admin(client, database):
    add_user(database, "admin", "administrator", ADMIN_PASSWORD)
    response = login(client, "admin", ADMIN_PASSWORD)
    assert response.status_code == 303
    return client


def count(database, model):
    with transaction(database) as session:
        return session.scalar(select(func.count()).select_from(model))


def test_login_sets_cookies_and_logout_revokes_refresh(client, database):
    add_user(database, "admin", "administrator", ADMIN_PASSWORD)
    response = login(client, "admin", ADMIN_PASSWORD)
    assert response.status_code == 303
    assert response.headers["location"] == "/students"
    assert client.cookies.get("access_token")
    refresh = client.cookies.get("refresh_token")
    assert refresh

    assert client.get("/students").status_code == 200

    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert client.cookies.get("access_token") is None
    with transaction(database) as session:
        row = session.scalar(select(RefreshSession).where(
            RefreshSession.token_digest == token_digest(refresh)))
        assert row.revoked_at is not None
    assert client.get("/students", follow_redirects=False).status_code == 303


def test_wrong_password_is_rejected_without_cookies(client, database):
    add_user(database, "admin", "administrator", ADMIN_PASSWORD)
    response = login(client, "admin", "wrong-password")
    assert response.status_code == 401
    assert "Неверный логин или пароль" in response.text
    assert client.cookies.get("access_token") is None


def test_unknown_login_is_rejected(client, database):
    response = login(client, "nobody", "whatever-1")
    assert response.status_code == 401
    assert "Неверный логин или пароль" in response.text


def test_inactive_account_cannot_login(client, database):
    add_user(database, "blocked", "student", PASSWORD, active=False)
    response = login(client, "blocked", PASSWORD)
    assert response.status_code == 403
    assert "заблокирована" in response.text
    assert client.cookies.get("access_token") is None


def test_protected_page_redirects_to_login(client):
    response = client.get("/students", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_creates_student_with_account_and_audit(admin, database):
    response = admin.post("/students/new", data=STUDENT_FORM, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/students?created=1"

    with transaction(database) as session:
        student = session.scalar(select(Student).where(Student.last_name == "Иванов"))
        assert student is not None
        assert student.group_name == "241-3211"
        account = session.get(User, student.user_id)
        assert account.role == "student"
        assert account.password_hash != STUDENT_FORM["password"]
        audit = session.scalar(select(AuditLog).where(AuditLog.object_id == student.id))
        assert audit.operation == "student.create"
        assert audit.result == "success"

    page = admin.get("/students?created=1")
    assert page.status_code == 200
    assert "Иванов" in page.text
    assert "241-3211" in page.text
    assert "Студент добавлен" in page.text


@pytest.mark.parametrize("field,value,message", [
    ("last_name", "", "Укажите фамилию"),
    ("admission_year", "24", "четыре цифры"),
    ("admission_year", "1800", "от 1900"),
    ("education_form", "вечерняя", "Выберите форму обучения"),
    ("login", "иван", "Логин"),
    ("password", "short", "Пароль"),
])
def test_student_form_validation(admin, database, field, value, message):
    data = dict(STUDENT_FORM)
    data[field] = value
    response = admin.post("/students/new", data=data)
    assert response.status_code == 400
    assert message in response.text
    assert count(database, Student) == 0
    assert count(database, AuditLog) == 0


def test_duplicate_login_is_rejected(admin, database):
    assert admin.post("/students/new", data=STUDENT_FORM,
                      follow_redirects=False).status_code == 303
    second = dict(STUDENT_FORM)
    second["last_name"] = "Петров"
    response = admin.post("/students/new", data=second)
    assert response.status_code == 400
    assert "Логин уже занят" in response.text
    assert count(database, Student) == 1


def test_student_sees_only_own_record(client, database):
    own_id = add_user(database, "s-own", "student")
    other_id = add_user(database, "s-other", "student")
    add_student(database, own_id, "Собственный", "s-own")
    add_student(database, other_id, "Чужой", "s-other")

    assert login(client, "s-own").status_code == 303
    page = client.get("/students")
    assert "Собственный" in page.text
    assert "Чужой" not in page.text
    assert client.get("/students/new", follow_redirects=False).status_code == 403


def test_teacher_sees_all_but_cannot_create(client, database):
    add_user(database, "teacher", "teacher")
    first = add_user(database, "s-1", "student")
    second = add_user(database, "s-2", "student")
    add_student(database, first, "Первый", "s-1")
    add_student(database, second, "Второй", "s-2")

    assert login(client, "teacher").status_code == 303
    page = client.get("/students")
    assert "Первый" in page.text and "Второй" in page.text
    assert client.get("/students/new", follow_redirects=False).status_code == 403
    assert client.post("/students/new", data=STUDENT_FORM,
                       follow_redirects=False).status_code == 403


def test_refresh_rotates_token(client, database):
    add_user(database, "admin", "administrator", ADMIN_PASSWORD)
    assert login(client, "admin", ADMIN_PASSWORD).status_code == 303
    old_refresh = client.cookies.get("refresh_token")

    response = client.post("/refresh", follow_redirects=False)
    assert response.status_code == 303
    new_refresh = client.cookies.get("refresh_token")
    assert new_refresh and new_refresh != old_refresh

    with transaction(database) as session:
        old_row = session.scalar(select(RefreshSession).where(
            RefreshSession.token_digest == token_digest(old_refresh)))
        assert old_row.revoked_at is not None
    assert client.get("/students").status_code == 200


def _student_id(database, last_name):
    with transaction(database) as session:
        return session.scalar(select(Student.id).where(Student.last_name == last_name))


def test_admin_edits_student_and_writes_audit(admin, database):
    assert admin.post("/students/new", data=STUDENT_FORM,
                      follow_redirects=False).status_code == 303
    student_id = _student_id(database, "Иванов")

    form = admin.get(f"/students/{student_id}/edit")
    assert form.status_code == 200
    assert "241-3211" in form.text

    response = admin.post(f"/students/{student_id}/edit", data={
        "last_name": "Иванов",
        "first_name": "Иван",
        "patronymic": "Иванович",
        "admission_year": "2026",
        "education_form": "заочная",
        "group_name": "241-9999",
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/students?updated=1"

    with transaction(database) as session:
        student = session.get(Student, student_id)
        assert student.group_name == "241-9999"
        assert student.admission_year == 2026
        assert student.education_form == "заочная"
        audit = session.scalar(select(AuditLog).where(
            AuditLog.object_id == student_id, AuditLog.operation == "student.update"))
        assert audit is not None

    page = admin.get("/students?updated=1")
    assert "Изменения сохранены" in page.text


def test_edit_validation_keeps_old_values(admin, database):
    assert admin.post("/students/new", data=STUDENT_FORM,
                      follow_redirects=False).status_code == 303
    student_id = _student_id(database, "Иванов")

    response = admin.post(f"/students/{student_id}/edit", data={
        "last_name": "Иванов",
        "first_name": "Иван",
        "patronymic": "",
        "admission_year": "1800",
        "education_form": "очная",
        "group_name": "241-0000",
    })
    assert response.status_code == 400
    assert "от 1900" in response.text
    with transaction(database) as session:
        assert session.get(Student, student_id).group_name == "241-3211"


def test_teacher_and_student_cannot_edit(client, database):
    teacher_id = add_user(database, "teacher", "teacher")
    add_student(database, teacher_id, "Учитель", "teacher")
    student_id = _student_id(database, "Учитель")

    assert login(client, "teacher").status_code == 303
    assert client.get(f"/students/{student_id}/edit", follow_redirects=False).status_code == 403
    assert client.post(f"/students/{student_id}/edit", data=STUDENT_FORM,
                       follow_redirects=False).status_code == 403

    client.post("/logout", follow_redirects=False)
    own_id = add_user(database, "s-own", "student")
    add_student(database, own_id, "Собственный", "s-own")
    own_student_id = _student_id(database, "Собственный")
    assert login(client, "s-own").status_code == 303
    assert client.get(f"/students/{own_student_id}/edit",
                      follow_redirects=False).status_code == 403


def test_edit_unknown_student_returns_404(admin):
    assert admin.get(f"/students/{uuid4()}/edit").status_code == 404
