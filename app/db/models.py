"""APP-01 entities. Authentication and product operations arrive in later PRs."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, MetaData, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher', 'administrator')", name="role"),
        CheckConstraint("length(trim(login)) > 0", name="login_not_blank"),
        CheckConstraint("length(trim(password_hash)) > 0", name="hash_not_blank"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(128), unique=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint("admission_year BETWEEN 1 AND 9999", name="admission_year"),
        CheckConstraint("length(trim(last_name)) > 0 AND length(trim(first_name)) > 0", name="name_not_blank"),
        CheckConstraint("length(trim(education_form)) > 0 AND length(trim(group_name)) > 0", name="study_not_blank"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), unique=True)
    last_name: Mapped[str] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    patronymic: Mapped[str | None] = mapped_column(String(100))
    admission_year: Mapped[int] = mapped_column(Integer)
    education_form: Mapped[str] = mapped_column(String(64))
    group_name: Mapped[str] = mapped_column(String(64))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("length(trim(operation)) > 0 AND length(trim(object_type)) > 0", name="operation_not_blank"),
        CheckConstraint("result IN ('success', 'failure')", name="result"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    operation: Mapped[str] = mapped_column(String(64))
    object_type: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[UUID] = mapped_column(Uuid)
    result: Mapped[str] = mapped_column(String(16))


class RefreshSession(Base):
    """Store only a SHA-256 token digest, never a bearer token (APP-02 contract)."""
    __tablename__ = "refresh_sessions"
    __table_args__ = (
        CheckConstraint("token_digest ~ '^[0-9a-f]{64}$'", name="digest_format"),
        CheckConstraint("expires_at > created_at", name="expiry"),
        CheckConstraint("revoked_at IS NULL OR revoked_at >= created_at", name="revocation"),
    )
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
