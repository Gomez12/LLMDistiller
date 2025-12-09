"""Configuration management for LLM Distiller."""

import os
from typing import Dict, Optional

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(default="sqlite:///./llm_distiller.db", description="Database URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    requests_per_minute: int = Field(
        default=60, description="Maximum requests per minute"
    )
    requests_per_hour: int = Field(
        default=1000, description="Maximum requests per hour"
    )
    tokens_per_minute: int = Field(
        default=40000, description="Maximum tokens per minute"
    )
    retry_after_seconds: int = Field(
        default=60, description="Seconds to wait after rate limit"
    )


class GenerationConfig(BaseModel):
    """LLM generation parameters."""

    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1000, ge=1, description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Presence penalty"
    )


class ProviderConfig(BaseModel):
    """Configuration for individual LLM providers."""

    type: str = Field(description="Provider type: 'openai', 'azure_openai', 'custom'")
    api_key: str = Field(
        default="", description="API key (empty = use environment variable)"
    )
    base_url: str = Field(default="", description="Custom base URL for API")
    model: str = Field(default="gpt-3.5-turbo", description="Model name")
    rate_limit: RateLimitConfig = Field(
        default_factory=RateLimitConfig, description="Rate limiting settings"
    )
    generation_params: GenerationConfig = Field(
        default_factory=GenerationConfig, description="Generation parameters"
    )

    def get_api_key(self) -> str:
        """Get API key from config or environment variable."""
        if self.api_key:
            return self.api_key

        # Try environment variable based on provider type
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "azure_openai": "AZURE_OPENAI_API_KEY",
        }

        env_var = env_var_map.get(self.type, f"{self.type.upper()}_API_KEY")
        return os.getenv(env_var, "")


class ProcessingConfig(BaseModel):
    """Processing configuration."""

    batch_size: int = Field(
        default=10, description="Number of questions to process in parallel"
    )
    max_retries: int = Field(
        default=3, description="Maximum retry attempts for failed requests"
    )
    timeout_seconds: int = Field(default=120, description="Request timeout in seconds")
    validate_responses: bool = Field(
        default=True, description="Enable JSON schema validation"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )


class Settings(BaseModel):
    """Global settings with hierarchical override support."""

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm_providers: Dict[str, ProviderConfig] = Field(
        default_factory=dict, description="LLM provider configurations"
    )
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from file with environment overrides."""
        # For now, return default settings
        # In a full implementation, this would load from config file
        return cls()

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get provider config by name."""
        return self.llm_providers.get(provider_name)

    def add_provider(self, name: str, config: ProviderConfig) -> None:
        """Add or update a provider configuration."""
        self.llm_providers[name] = config
