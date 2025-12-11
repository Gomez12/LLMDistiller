"""Unit tests for configuration settings."""

import os
from unittest.mock import patch

import pytest

from llm_distiller.config.settings import (
    DatabaseConfig,
    GenerationConfig,
    LoggingConfig,
    ProcessingConfig,
    ProviderConfig,
    RateLimitConfig,
    Settings,
)


class TestDatabaseConfig:
    """Test DatabaseConfig."""

    def test_database_config_defaults(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.url == "sqlite:///./llm_distiller.db"
        assert config.echo is False

    def test_database_config_custom(self):
        """Test custom database configuration."""
        config = DatabaseConfig(
            url="postgresql://user:pass@localhost/db",
            echo=True
        )
        
        assert config.url == "postgresql://user:pass@localhost/db"
        assert config.echo is True


class TestRateLimitConfig:
    """Test RateLimitConfig."""

    def test_rate_limit_config_defaults(self):
        """Test default rate limit configuration."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.tokens_per_minute == 40000
        assert config.retry_after_seconds == 60

    def test_rate_limit_config_custom(self):
        """Test custom rate limit configuration."""
        config = RateLimitConfig(
            requests_per_minute=30,
            tokens_per_minute=20000
        )
        
        assert config.requests_per_minute == 30
        assert config.requests_per_hour == 1000  # Default
        assert config.tokens_per_minute == 20000


class TestGenerationConfig:
    """Test GenerationConfig."""

    def test_generation_config_defaults(self):
        """Test default generation configuration."""
        config = GenerationConfig()
        
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.top_p == 1.0
        assert config.frequency_penalty == 0.0
        assert config.presence_penalty == 0.0

    def test_generation_config_validation(self):
        """Test generation parameter validation."""
        # Valid values
        config = GenerationConfig(
            temperature=1.5,
            max_tokens=2000,
            top_p=0.9
        )
        assert config.temperature == 1.5
        assert config.max_tokens == 2000
        assert config.top_p == 0.9
        
        # Invalid temperature (should raise ValidationError)
        with pytest.raises(Exception):
            GenerationConfig(temperature=3.0)  # > 2.0
        
        # Invalid max_tokens (should raise ValidationError)
        with pytest.raises(Exception):
            GenerationConfig(max_tokens=0)  # < 1


class TestProviderConfig:
    """Test ProviderConfig."""

    def test_provider_config_defaults(self):
        """Test default provider configuration."""
        config = ProviderConfig(type="openai")
        
        assert config.type == "openai"
        assert config.api_key == ""
        assert config.base_url == ""
        assert config.model == "gpt-3.5-turbo"
        assert isinstance(config.rate_limit, RateLimitConfig)
        assert isinstance(config.generation_params, GenerationConfig)

    def test_provider_config_custom(self):
        """Test custom provider configuration."""
        rate_limit = RateLimitConfig(requests_per_minute=30)
        generation = GenerationConfig(temperature=0.5)
        
        config = ProviderConfig(
            type="azure_openai",
            api_key="test-key",
            base_url="https://test.openai.azure.com",
            model="gpt-4",
            rate_limit=rate_limit,
            generation_params=generation
        )
        
        assert config.type == "azure_openai"
        assert config.api_key == "test-key"
        assert config.base_url == "https://test.openai.azure.com"
        assert config.model == "gpt-4"
        assert config.rate_limit.requests_per_minute == 30
        assert config.generation_params.temperature == 0.5

    def test_get_api_key_from_config(self):
        """Test getting API key from config."""
        config = ProviderConfig(type="openai", api_key="config-key")
        assert config.get_api_key() == "config-key"

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'})
    def test_get_api_key_from_environment(self):
        """Test getting API key from environment variable."""
        config = ProviderConfig(type="openai", api_key="")
        assert config.get_api_key() == "env-key"

    @patch.dict(os.environ, {'AZURE_OPENAI_API_KEY': 'azure-key'})
    def test_get_azure_api_key_from_environment(self):
        """Test getting Azure API key from environment variable."""
        config = ProviderConfig(type="azure_openai", api_key="")
        assert config.get_api_key() == "azure-key"

    def test_get_api_key_missing(self):
        """Test getting API key when not set."""
        config = ProviderConfig(type="openai", api_key="")
        assert config.get_api_key() == ""


class TestProcessingConfig:
    """Test ProcessingConfig."""

    def test_processing_config_defaults(self):
        """Test default processing configuration."""
        config = ProcessingConfig()
        
        assert config.batch_size == 10
        assert config.max_retries == 3
        assert config.timeout_seconds == 120
        assert config.validate_responses is True

    def test_processing_config_custom(self):
        """Test custom processing configuration."""
        config = ProcessingConfig(
            batch_size=5,
            max_retries=5,
            timeout_seconds=60,
            validate_responses=False
        )
        
        assert config.batch_size == 5
        assert config.max_retries == 5
        assert config.timeout_seconds == 60
        assert config.validate_responses is False


class TestLoggingConfig:
    """Test LoggingConfig."""

    def test_logging_config_defaults(self):
        """Test default logging configuration."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.file_path is None
        assert "%(asctime)s" in config.format

    def test_logging_config_custom(self):
        """Test custom logging configuration."""
        config = LoggingConfig(
            level="DEBUG",
            file_path="/tmp/test.log",
            format="%(levelname)s - %(message)s"
        )
        
        assert config.level == "DEBUG"
        assert config.file_path == "/tmp/test.log"
        assert config.format == "%(levelname)s - %(message)s"


class TestSettings:
    """Test main Settings class."""

    def test_settings_defaults(self):
        """Test default settings."""
        settings = Settings()
        
        assert isinstance(settings.database, DatabaseConfig)
        assert isinstance(settings.processing, ProcessingConfig)
        assert isinstance(settings.logging, LoggingConfig)
        assert settings.llm_providers == {}

    def test_settings_custom(self):
        """Test custom settings."""
        provider = ProviderConfig(type="openai", api_key="test-key")
        
        settings = Settings(
            database=DatabaseConfig(echo=True),
            llm_providers={"test": provider},
            processing=ProcessingConfig(batch_size=5),
            logging=LoggingConfig(level="DEBUG")
        )
        
        assert settings.database.echo is True
        assert settings.llm_providers["test"] == provider
        assert settings.processing.batch_size == 5
        assert settings.logging.level == "DEBUG"

    def test_get_provider_config(self):
        """Test getting provider configuration."""
        provider = ProviderConfig(type="openai", api_key="test-key")
        settings = Settings(llm_providers={"test": provider})
        
        assert settings.get_provider_config("test") == provider
        assert settings.get_provider_config("nonexistent") is None

    def test_add_provider(self):
        """Test adding a provider."""
        settings = Settings()
        provider = ProviderConfig(type="openai", api_key="test-key")
        
        settings.add_provider("test", provider)
        
        assert "test" in settings.llm_providers
        assert settings.llm_providers["test"] == provider

    def test_add_provider_update(self):
        """Test updating an existing provider."""
        provider1 = ProviderConfig(type="openai", api_key="key1")
        provider2 = ProviderConfig(type="openai", api_key="key2")
        
        settings = Settings(llm_providers={"test": provider1})
        settings.add_provider("test", provider2)  # Should update
        
        assert settings.llm_providers["test"] == provider2

    def test_load_method(self):
        """Test the load class method."""
        settings = Settings.load()
        
        assert isinstance(settings, Settings)
        # Should return default settings for now