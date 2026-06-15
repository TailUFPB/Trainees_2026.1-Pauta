"""Garante uma única linha de migrations após integrar timeline e notificações."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_migrations_possuem_head_unico_0014() -> None:
    server_dir = Path(__file__).parents[1]
    config = Config(server_dir / "alembic.ini")
    config.set_main_option("script_location", str(server_dir / "alembic"))
    scripts = ScriptDirectory.from_config(config)

    assert scripts.get_heads() == ["0014"]

    revisions = [revision.revision for revision in scripts.walk_revisions()]
    assert len(revisions) == len(set(revisions))
