"""Database configuration and engine setup."""

import logging
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

# Configure SQLAlchemy logging
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.engine")


class DatabaseConfig:
    """Database configuration and session management."""

    def __init__(
        self,
        database_url: str = "sqlite:///./sqlalchemy_practice.db",
        echo: bool = False,
        pool_class: type[NullPool | QueuePool | StaticPool] | None = None,
        **engine_kwargs: Any,
    ):
        """
        Initialize database configuration.

        Args:
            database_url: Database connection URL
            echo: Enable SQL query logging
            pool_class: Connection pool class (NullPool, QueuePool, StaticPool)
            **engine_kwargs: Additional engine configuration options
        """
        self.database_url = database_url
        self.echo = echo

        engine_options: dict[str, Any] = {
            "echo": echo,
            "future": True,  # Enable SQLAlchemy 2.0 style
        }

        if pool_class:
            engine_options["poolclass"] = pool_class

        engine_options.update(engine_kwargs)

        self.engine = create_engine(database_url, **engine_options)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        # Enable query logging if echo is True
        if echo:
            self._setup_query_logging()

    def _setup_query_logging(self) -> None:
        """Configure detailed query logging."""
        logger.setLevel(logging.INFO)

        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(  # type: ignore[reportUnusedFunction]
            _conn: Any,
            _cursor: Any,
            statement: str,
            params: Any,
            _context: Any,
            executemany: bool,
        ) -> None:
            """Log SQL statements before execution."""
            if executemany:
                logger.info("EXECUTEMANY: %s", statement)
            else:
                logger.info("EXECUTE: %s | PARAMS: %s", statement, params)

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()

    def close(self) -> None:
        """Close the database engine and all connections."""
        self.engine.dispose()


# Default database instance for development
db = DatabaseConfig()
