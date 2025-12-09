"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from ..config import GenerationConfig, ProviderConfig

if TYPE_CHECKING:
    from ..utils.rate_limiter import RateLimiter


class ParsedResponse:
    """Parsed and normalized LLM response."""

    def __init__(
        self,
        content: str,
        tokens_used: Optional[int] = None,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.tokens_used = tokens_used
        self.model = model
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<ParsedResponse(model='{self.model}', tokens={self.tokens_used})>"


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    async def generate_response(
        self, prompt: str, generation_config: GenerationConfig
    ) -> ParsedResponse:
        """Generate response from LLM.

        Args:
            prompt: Input prompt for the LLM
            generation_config: Generation parameters

        Returns:
            Parsed response with content and metadata
        """

    @abstractmethod
    def get_rate_limiter(self) -> Optional["RateLimiter"]:
        """Get provider-specific rate limiter."""

    @abstractmethod
    def parse_response(self, raw_response: Any) -> ParsedResponse:
        """Parse and normalize provider response.

        Args:
            raw_response: Raw response from provider API

        Returns:
            Normalized parsed response
        """

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return self.config.type

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.config.model
