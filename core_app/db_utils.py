import asyncpg
from urllib.parse import urlparse
from sqlalchemy.engine import make_url


def make_test_database_url(production_url: str, test_db_name: str, host: str = "localhost") -> str:
    url = make_url(production_url)
    return url.set(database=test_db_name, host=host).render_as_string(hide_password=False)


async def ensure_test_database(test_database_url: str, admin_url: str | None = None) -> None:
    """Create test database if it doesn't exist.

    Args:
        test_database_url: async URL like postgresql+asyncpg://user:pass@host/dbname
        admin_url: sync URL to postgres default DB. If None, derived from test_database_url.
    """
    parsed = urlparse(test_database_url)
    db_name = parsed.path.lstrip("/")

    if admin_url is None:
        admin_url = (
            f"postgresql://{parsed.username}:{parsed.password}"
            f"@{parsed.hostname}:{parsed.port or 5432}/postgres"
        )

    conn = await asyncpg.connect(admin_url)
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = $1", db_name
    )
    if not exists:
        await conn.execute(f'CREATE DATABASE "{db_name}"')
    await conn.close()
