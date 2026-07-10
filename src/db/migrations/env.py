"""Alembic environment — migrations run over the DIRECT (unpooled) connection."""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.config import get_settings
from src.db.base import Base
from src.db.engine import to_sqlalchemy_url
from src.db.models import ActText, GazetteItem  # noqa: F401 — register tables on the metadata

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    settings = get_settings()
    url = settings.database_url_direct or settings.database_url
    if not url:
        raise RuntimeError("Set DATABASE_URL_DIRECT (or DATABASE_URL) to run migrations.")
    return to_sqlalchemy_url(url)


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _url()
    connectable = engine_from_config(configuration, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, include_schemas=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
