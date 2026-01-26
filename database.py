"""
Database connection and session management.
Supports direct PostgreSQL connection or SSH tunnel for PythonAnywhere.
"""

from contextlib import contextmanager
from typing import Generator, Optional

import sshtunnel
from sqlmodel import SQLModel, Session, create_engine

from config import get_settings

# Module-level engine (initialized lazily)
_engine = None
_tunnel: Optional[sshtunnel.SSHTunnelForwarder] = None


def _create_ssh_tunnel() -> sshtunnel.SSHTunnelForwarder:
    """Create SSH tunnel for database connection."""
    settings = get_settings()

    sshtunnel.SSH_TIMEOUT = settings.SSH_TIMEOUT
    sshtunnel.TUNNEL_TIMEOUT = settings.TUNNEL_TIMEOUT

    tunnel = sshtunnel.SSHTunnelForwarder(
        ("ssh.pythonanywhere.com",),
        ssh_username=settings.PA_USERNAME,
        ssh_password=settings.PA_PASSWORD,
        remote_bind_address=(settings.PG_HOST, settings.PG_PORT),
    )
    tunnel.start()
    return tunnel


def _get_database_url() -> str:
    """Get database URL, creating SSH tunnel if necessary."""
    global _tunnel
    settings = get_settings()

    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    if settings.use_ssh_tunnel:
        if _tunnel is None or not _tunnel.is_active:
            _tunnel = _create_ssh_tunnel()
        return (
            f"postgresql://{settings.PG_USER}:{settings.PG_PASS}"
            f"@127.0.0.1:{_tunnel.local_bind_port}/{settings.PG_DB}"
        )

    return (
        f"postgresql://{settings.PG_USER}:{settings.PG_PASS}"
        f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DB}"
    )


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        database_url = _get_database_url()
        _engine = create_engine(
            database_url,
            echo=get_settings().DEBUG,
            pool_pre_ping=True,
        )
    return _engine


def create_db_and_tables() -> None:
    """Create all database tables."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    engine = get_engine()
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def close_connections() -> None:
    """Close database connections and SSH tunnel."""
    global _engine, _tunnel

    if _engine is not None:
        _engine.dispose()
        _engine = None

    if _tunnel is not None and _tunnel.is_active:
        _tunnel.stop()
        _tunnel = None
