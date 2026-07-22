"""Alembic migration environment.

Resolves the database URL from (in order) the alembic ``-x url=...`` option,
the ``DATABASE_URL`` environment variable, then a local SQLite default — so no
credential or environment coupling lives in source. ``target_metadata`` is the
ORM's ``Base.metadata`` so autogenerate and the schema-parity test stay honest.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from naismith_api.db import Base

config = context.config
target_metadata = Base.metadata


def _resolve_url() -> str:
    x_args = context.get_x_argument(as_dictionary=True)
    if "url" in x_args:
        return x_args["url"]
    from_ini = config.get_main_option("sqlalchemy.url")
    if from_ini:
        return from_ini
    return os.environ.get("DATABASE_URL", "sqlite:///./naismith.db")


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
