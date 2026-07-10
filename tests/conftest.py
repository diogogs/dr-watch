"""Shared fixtures. Integration tests need a database with the schema migrated.

Locally, pydantic-settings reads .env, so ``uv run pytest`` hits the project's own Neon
(tests use sentinel keys and clean up after themselves). In CI a throwaway Postgres service
provides the database; missing configuration there is a failure, never a silent skip.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.config import get_settings
from src.db.engine import make_engine, make_session_factory


@pytest.fixture(scope="session")
def pg_engine() -> Iterator[Engine]:
    if not get_settings().database_url:
        if os.environ.get("GITHUB_ACTIONS"):
            pytest.fail("DATABASE_URL must be configured in CI (postgres service)")
        pytest.skip("integration tests need DATABASE_URL (.env)")
    engine = make_engine()
    yield engine
    engine.dispose()


@pytest.fixture
def pg_session(pg_engine: Engine) -> Iterator[Session]:
    factory = make_session_factory(pg_engine)
    with factory() as session:
        yield session
