"""APP-01 initial persistence"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('login', sa.String(length=128), nullable=False),
    sa.Column('password_hash', sa.String(length=512), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.CheckConstraint("role IN ('student', 'teacher', 'administrator')", name=op.f('ck_users_role')),
    sa.CheckConstraint('length(trim(login)) > 0', name=op.f('ck_users_login_not_blank')),
    sa.CheckConstraint('length(trim(password_hash)) > 0', name=op.f('ck_users_hash_not_blank')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('login', name=op.f('uq_users_login'))
    )
    op.create_table('audit_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('operation', sa.String(length=64), nullable=False),
    sa.Column('object_type', sa.String(length=64), nullable=False),
    sa.Column('object_id', sa.Uuid(), nullable=False),
    sa.Column('result', sa.String(length=16), nullable=False),
    sa.CheckConstraint("result IN ('success', 'failure')", name=op.f('ck_audit_logs_result')),
    sa.CheckConstraint('length(trim(operation)) > 0 AND length(trim(object_type)) > 0', name=op.f('ck_audit_logs_operation_not_blank')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_table('refresh_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('token_digest', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("token_digest ~ '^[0-9a-f]{64}$'", name=op.f('ck_refresh_sessions_digest_format')),
    sa.CheckConstraint('expires_at > created_at', name=op.f('ck_refresh_sessions_expiry')),
    sa.CheckConstraint('revoked_at IS NULL OR revoked_at >= created_at', name=op.f('ck_refresh_sessions_revocation')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_refresh_sessions_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_refresh_sessions')),
    sa.UniqueConstraint('token_digest', name=op.f('uq_refresh_sessions_token_digest'))
    )
    op.create_index(op.f('ix_refresh_sessions_expires_at'), 'refresh_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_refresh_sessions_user_id'), 'refresh_sessions', ['user_id'], unique=False)
    op.create_table('students',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('patronymic', sa.String(length=100), nullable=True),
    sa.Column('admission_year', sa.Integer(), nullable=False),
    sa.Column('education_form', sa.String(length=64), nullable=False),
    sa.Column('group_name', sa.String(length=64), nullable=False),
    sa.CheckConstraint('admission_year BETWEEN 1 AND 9999', name=op.f('ck_students_admission_year')),
    sa.CheckConstraint('length(trim(education_form)) > 0 AND length(trim(group_name)) > 0', name=op.f('ck_students_study_not_blank')),
    sa.CheckConstraint('length(trim(last_name)) > 0 AND length(trim(first_name)) > 0', name=op.f('ck_students_name_not_blank')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_students_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_students')),
    sa.UniqueConstraint('user_id', name=op.f('uq_students_user_id'))
    )


def downgrade():
    op.drop_table('students')
    op.drop_index(op.f('ix_refresh_sessions_user_id'), table_name='refresh_sessions')
    op.drop_index(op.f('ix_refresh_sessions_expires_at'), table_name='refresh_sessions')
    op.drop_table('refresh_sessions')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_table('users')
