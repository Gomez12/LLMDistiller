"""Base LLM provider interface."""

import re
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
        thinking: Optional[str] = None,
    ):
        self.content = content
        self.tokens_used = tokens_used
        self.model = model
        self.metadata = metadata or {}
        self.thinking = thinking

    def __repr__(self) -> str:
        return f"<ParsedResponse(model='{self.model}', tokens={self.tokens_used})>"


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration (optional for utility usage)
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
        if not self.config:
            return "unknown"
        return getattr(self.config, 'type', 'unknown')

    @property
    def model_name(self) -> str:
        """Get model name."""
        if not self.config:
            return "unknown"
        return getattr(self.config, 'model', 'unknown')


class ThinkingExtractor:
    """Utility class for extracting thinking from LLM responses."""
    
    @staticmethod
    def extract_thinking(content: str, separate_reasoning: Optional[str] = None) -> tuple[str, Optional[str]]:
        """Extract thinking/reasoning from model response.
        
        Args:
            content: The full response content
            separate_reasoning: Separate reasoning context if provided by model
            
        Returns:
            Tuple of (cleaned_content, thinking)
        """
        thinking = None
        cleaned_content = content
        
        # If separate reasoning is provided, use it
        if separate_reasoning and separate_reasoning.strip():
            thinking = separate_reasoning.strip()
            return cleaned_content, thinking
        
        # Look for thinking tags in the content
        # Pattern: <thinking>...</thinking>
        thinking_pattern = r'<think>(.*?)</think>'
        thinking_match = re.search(thinking_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove thinking tags from content
            cleaned_content = re.sub(thinking_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            # Look for reasoning tags as fallback
            reasoning_pattern = r'<reason>(.*?)</reason>'
            reasoning_match = re.search(reasoning_pattern, content, re.DOTALL | re.IGNORECASE)
            
            if reasoning_match:
                thinking = reasoning_match.group(1).strip()
                # Remove reasoning tags from content
                cleaned_content = re.sub(reasoning_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        
        ##print("RAW CONTENT:", repr(content))
        ##print("THINKING MATCH:", thinking_match.group(0) if thinking_match else None)
        ##print("THINKING1 MATCH:", thinking_match.group(1) if thinking_match else None)
        ##print("RETURNING:", repr(cleaned_content), repr(thinking))
        return cleaned_content, thinking
