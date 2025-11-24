"""Database initialization utilities."""

from sqlalchemy import Engine

from ..models import Base


def create_tables(engine: Engine) -> None:
    """
    Create all tables in the database.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")


def drop_tables(engine: Engine) -> None:
    """
    Drop all tables from the database.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)
    print("✓ All tables dropped successfully")


def reset_database(engine: Engine) -> None:
    """
    Reset the database by dropping and recreating all tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    print("Resetting database...")
    drop_tables(engine)
    create_tables(engine)
    print("✓ Database reset complete")
