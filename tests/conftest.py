"""Pytest configuration and fixtures for LLM Distiller tests."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker

from llm_distiller.config.settings import (
    DatabaseConfig,
    LoggingConfig,
    ProcessingConfig,
    ProviderConfig,
    RateLimitConfig,
    Settings,
)
from llm_distiller.database.base import Base
from llm_distiller.database.manager import DatabaseManager


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test configuration settings."""
    return Settings(
        database=DatabaseConfig(
            url="sqlite:///:memory:",
            echo=False,
        ),
        llm_providers={
            "test_provider": ProviderConfig(
                type="openai",
                api_key="test-key",
                base_url="http://localhost:9999/v1",
                model="test-model",
                rate_limit=RateLimitConfig(
                    requests_per_minute=10,
                    tokens_per_minute=5000,
                ),
            )
        },
        processing=ProcessingConfig(
            batch_size=1,
            max_retries=3,
            timeout_seconds=30,
        ),
        logging=LoggingConfig(
            level="WARNING",
        ),
    )


@pytest.fixture
def test_db_engine(test_settings: Settings) -> Generator[sqlalchemy.Engine, None, None]:
    """Test database engine."""
    engine = sqlalchemy.create_engine(test_settings.database.url)
    Base.metadata.create_all(engine)
    
    yield engine
    
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_db_session(test_db_engine: sqlalchemy.Engine) -> Generator[Session, None, None]:
    """Test database session."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def test_db_manager(test_settings: Settings) -> DatabaseManager:
    """Test database manager."""
    return DatabaseManager(
        database_url=test_settings.database.url,
        echo=test_settings.database.echo,
        pool_size=test_settings.database.pool_size,
        max_overflow=test_settings.database.max_overflow,
        pool_pre_ping=test_settings.database.pool_pre_ping,
        pool_recycle=test_settings.database.pool_recycle,
    )


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Temporary configuration file."""
    config = {
        "database": {"url": "sqlite:///:memory:", "echo": False},
        "llm_providers": {
            "test": {
                "type": "openai",
                "api_key": "test-key",
                "model": "test-model",
            }
        },
        "processing": {
            "batch_size": 1,
            "max_retries": 3,
            "timeout_seconds": 30,
        },
        "logging": {
            "level": "WARNING",
        },
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def sample_questions() -> list[Dict[str, Any]]:
    """Sample question data for testing."""
    return [
        {
            "json_id": "1",
            "category": "math",
            "question": "What is 2+2?",
            "golden_answer": "4",
            "answer_schema": '{"type": "object", "properties": {"answer": {"type": "number"}}}',
        },
        {
            "json_id": "2",
            "category": "science",
            "question": "What is H2O?",
            "golden_answer": "Water",
            "answer_schema": '{"type": "object", "properties": {"answer": {"type": "string"}}}',
        },
        {
            "json_id": "3",
            "category": "history",
            "question": "When did World War II end?",
            "golden_answer": "1945",
            "answer_schema": '{"type": "object", "properties": {"answer": {"type": "string"}}}',
        },
    ]


@pytest.fixture
def sample_csv_file(sample_questions: list[Dict[str, Any]]) -> Generator[str, None, None]:
    """Temporary CSV file with sample questions."""
    import csv
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sample_questions[0].keys())
        writer.writeheader()
        writer.writerows(sample_questions)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"answer": "4"}',
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 56,
            "completion_tokens": 31,
            "total_tokens": 87,
        },
    }


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider for testing."""
    from unittest.mock import Mock
    
    provider = Mock()
    provider.generate_response.return_value = {
        "content": '{"answer": "4"}',
        "tokens_used": 87,
        "model": "test-model",
        "response_time": 0.5,
    }
    return provider


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup common test environment variables."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Temporary output directory for file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)