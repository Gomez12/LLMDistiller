"""Database connection and session management."""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base


class DatabaseManager:
    """Central database connection and session management."""

    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 20, 
                 max_overflow: int = 30, pool_pre_ping: bool = True, pool_recycle: int = 3600):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements
            pool_size: Database connection pool size
            max_overflow: Maximum overflow connections
            pool_pre_ping: Validate connections before use
            pool_recycle: Connection recycle time in seconds
        """
        self.engine = create_engine(
            database_url, 
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            pool_recycle=pool_recycle
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def async_session_scope(self) -> AsyncGenerator[Session, None]:
        """Provide an async transactional scope around a series of operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def execute_with_retry(self, operation, max_retries: int = 3):
        """Execute database operation with retry logic."""
        for attempt in range(max_retries):
            try:
                async with self.async_session_scope() as session:
                    return operation(session)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                # In a real implementation, you might want to add exponential backoff
                continue
