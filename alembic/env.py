from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import sqlalchemy as sa
from alembic import op

from alembic import context
from app.db.database import Base
from app.models.user import User
from app.models.team_member import Team, TeamMember, TeamInvite, TeamProject, PasswordResetToken
from app.models.task import Task
from app.models.backlog import Sprint, BacklogItem

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with DATABASE_URL env var if available
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

def upgrade():
    op.create_table('team_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(), default='member'),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
    )
    op.create_table('team_invites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('token', sa.String(), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('accepted', sa.Integer(), default=0),
    )
    op.create_table('team_projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table('password_reset_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('used', sa.Integer(), default=0),
    )
    # Add new columns to tasks
    op.add_column('tasks', sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('tasks', sa.Column('project_id', sa.Integer(), sa.ForeignKey('team_projects.id'), nullable=True))

def downgrade():
    op.drop_column('tasks', 'project_id')
    op.drop_column('tasks', 'assigned_to')
    op.drop_table('password_reset_tokens')
    op.drop_table('team_projects')
    op.drop_table('team_invites')
    op.drop_table('team_members')
