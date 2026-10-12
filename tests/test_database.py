from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import DataError, IntegrityError

from app.db.models import User, Student, AuditLog, RefreshSession
from app.db.session import transaction

pytestmark = pytest.mark.integration


def user(**kwargs):
    return User(login="fixture-" + uuid4().hex, password_hash="synthetic-hash-not-an-account", role="student", **kwargs)


def student(user_id):
    return Student(user_id=user_id, last_name="Тестовый", first_name="Студент",
                   admission_year=2026, education_form="очная", group_name="ТЕСТ")


def test_schema_matches_models_and_roundtrip(database):
    command.check(Config("alembic.ini"))
    assert set(inspect(database).get_table_names()) == {"users", "students", "audit_logs", "refresh_sessions", "alembic_version"}
    command.downgrade(Config("alembic.ini"), "base")
    assert inspect(database).get_table_names() == ["alembic_version"]
    command.upgrade(Config("alembic.ini"), "head")
    command.check(Config("alembic.ini"))


def test_committed_data_survives_new_connection(database):
    with transaction(database) as session:
        u = user(); session.add(u); session.flush()
        s = student(u.id); session.add(s); session.flush()
        session.add(AuditLog(user_id=u.id, operation="student.create", object_type="student", object_id=s.id, result="success"))
    database.dispose()
    with transaction(database) as session:
        assert session.scalar(select(func.count()).select_from(Student)) == 1
        assert session.scalar(select(func.count()).select_from(AuditLog)) == 1


def test_failure_rolls_back_data_and_audit(database):
    with pytest.raises(IntegrityError), transaction(database) as session:
        u = user(); session.add(u); session.flush()
        s = student(u.id); session.add(s); session.flush()
        session.add(AuditLog(user_id=u.id, operation="student.create", object_type="student", object_id=s.id, result="success"))
        session.flush()
        session.add(student(u.id))  # violates User–Student 1:1
    with transaction(database) as session:
        for model in (User, Student, AuditLog):
            assert session.scalar(select(func.count()).select_from(model)) == 0
        session.add(user())  # a subsequent transaction still succeeds


@pytest.mark.parametrize("model", ["student", "audit", "refresh"])
def test_foreign_keys_reject_missing_users(database, model):
    missing = uuid4()
    records = {
        "student": student(missing),
        "audit": AuditLog(user_id=missing, operation="test", object_type="student", object_id=uuid4(), result="success"),
        "refresh": RefreshSession(user_id=missing, token_digest="a"*64, expires_at=datetime.now(timezone.utc)+timedelta(days=1)),
    }
    with pytest.raises(IntegrityError), transaction(database) as session:
        session.add(records[model])


def test_user_delete_is_restricted(database):
    with transaction(database) as session:
        u = user(); session.add(u); session.flush(); uid = u.id
        session.add(student(uid))
    with pytest.raises(IntegrityError), transaction(database) as session:
        session.delete(session.get(User, uid))


@pytest.mark.parametrize("field,value", [("role", "root"), ("login", " "), ("password_hash", "")])
def test_user_constraints(database, field, value):
    u = user(); setattr(u, field, value)
    with pytest.raises(IntegrityError), transaction(database) as session:
        session.add(u)


def test_duplicate_login_rejected(database):
    with transaction(database) as session:
        u = user(); session.add(u); login = u.login
    with pytest.raises(IntegrityError), transaction(database) as session:
        duplicate = user(); duplicate.login = login; session.add(duplicate)


def test_refresh_revocation_persists(database):
    with transaction(database) as session:
        u = user(); session.add(u); session.flush()
        token = RefreshSession(user_id=u.id, token_digest="b"*64, expires_at=datetime.now(timezone.utc)+timedelta(days=1))
        session.add(token); session.flush(); tid = token.id
    with transaction(database) as session:
        session.get(RefreshSession, tid).revoked_at = datetime.now(timezone.utc)
    with transaction(database) as session:
        assert session.get(RefreshSession, tid).revoked_at is not None
    assert "token" not in {column["name"] for column in inspect(database).get_columns("refresh_sessions")}


@pytest.mark.parametrize("field,value", [("token_digest", "raw-bearer-token"), ("expires_at", datetime(2000,1,1,tzinfo=timezone.utc))])
def test_refresh_constraints(database, field, value):
    with transaction(database) as session:
        u = user(); session.add(u); session.flush(); uid = u.id
    token = RefreshSession(user_id=uid, token_digest="a"*64, expires_at=datetime.now(timezone.utc)+timedelta(days=1))
    setattr(token, field, value)
    with pytest.raises(IntegrityError), transaction(database) as session:
        session.add(token)


@pytest.mark.parametrize("field,value", [("admission_year", 0), ("first_name", " "), ("group_name", ""), ("last_name", "x"*101)])
def test_student_constraints(database, field, value):
    with transaction(database) as session:
        u = user(); session.add(u); session.flush(); uid = u.id
    record = student(uid); setattr(record, field, value)
    with pytest.raises((IntegrityError, DataError)), transaction(database) as session:
        session.add(record)


def test_sql_characters_are_stored_as_data(database):
    login = "'; DROP TABLE users; --"
    with transaction(database) as session:
        u = user(); u.login = login; session.add(u)
    with transaction(database) as session:
        assert session.scalar(select(User).where(User.login == login)).login == login
