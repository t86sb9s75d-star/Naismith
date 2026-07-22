"""Alembic migration parity: ``upgrade head`` must build exactly the ORM schema.

Guards against migration/model drift — add a column to db.py but forget the
migration (or vice versa) and this fails. It runs the real migration against a
throwaway SQLite file, so Alembic is exercised in CI, not just shipped.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from naismith_api.db import Base

_API_ROOT = Path(__file__).resolve().parents[1]
_ALEMBIC_INI = _API_ROOT / "alembic.ini"


def _model_schema() -> dict[str, set[str]]:
    return {
        name: set(table.columns.keys()) for name, table in Base.metadata.tables.items()
    }


def test_upgrade_head_matches_orm_schema(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", url)

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names()) - {"alembic_version"}
        model = _model_schema()
        assert tables == set(model), f"table drift: {tables ^ set(model)}"
        for table, columns in model.items():
            got = {c["name"] for c in inspector.get_columns(table)}
            assert got == columns, f"{table} column drift: {got ^ columns}"
    finally:
        engine.dispose()
