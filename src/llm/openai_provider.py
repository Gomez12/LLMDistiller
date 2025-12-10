"""OpenAI LLM provider implementation."""

import time
from typing import Any, Dict, Optional, TYPE_CHECKING

import openai
from openai import AsyncOpenAI

from ..config import GenerationConfig, ProviderConfig
from .base import BaseLLMProvider, ParsedResponse

if TYPE_CHECKING:
    from ..utils.rate_limiter import RateLimiter


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)

        api_key = config.get_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is required")

        client_kwargs = {"api_key": api_key}
        if config.base_url:
            client_kwargs["base_url"] = config.base_url

        self.client = AsyncOpenAI(**client_kwargs)

    async def generate_response(
        self, prompt: str, generation_config: GenerationConfig
    ) -> ParsedResponse:
        """Generate response from OpenAI API.

        Args:
            prompt: Input prompt for the LLM
            generation_config: Generation parameters

        Returns:
            Parsed response with content and metadata
        """
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=generation_config.temperature,
                max_tokens=generation_config.max_tokens,
                top_p=generation_config.top_p,
                frequency_penalty=generation_config.frequency_penalty,
                presence_penalty=generation_config.presence_penalty,
            )

            processing_time = int((time.time() - start_time) * 1000)

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Extract thinking from response
            # Check if model provides separate reasoning (e.g., in message.reasoning or similar)
            separate_reasoning = None
            message = response.choices[0].message
            if hasattr(message, 'reasoning') and getattr(message, 'reasoning', None):
                separate_reasoning = getattr(message, 'reasoning')
            
            # Extract thinking using ThinkingExtractor
            from .base import ThinkingExtractor
            cleaned_content, thinking = ThinkingExtractor.extract_thinking(content, separate_reasoning)

            return ParsedResponse(
                content=cleaned_content,
                tokens_used=tokens_used,
                model=response.model,
                thinking=thinking,
                metadata={
                    "processing_time_ms": processing_time,
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": (
                        response.usage.prompt_tokens if response.usage else None
                    ),
                    "completion_tokens": (
                        response.usage.completion_tokens if response.usage else None
                    ),
                },
            )

        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {e}")
        except openai.RateLimitError as e:
            raise Exception(f"OpenAI rate limit exceeded: {e}")
        except openai.AuthenticationError as e:
            raise Exception(f"OpenAI authentication error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error generating response: {e}")

    def get_rate_limiter(self) -> Optional["RateLimiter"]:
        """Get OpenAI-specific rate limiter."""
        from ..utils.rate_limiter import RateLimiter
        return RateLimiter(self.config.rate_limit, "openai")

    def parse_response(self, raw_response: Any) -> ParsedResponse:
        """Parse OpenAI API response.
        
        Args:
            raw_response: Raw response from OpenAI API
            
        Returns:
            Normalized parsed response
        """
        # This method is used when we have a raw response that needs parsing
        # For the async client, we handle parsing directly in generate_response
        content = raw_response.choices[0].message.content or ""
        tokens_used = raw_response.usage.total_tokens if raw_response.usage else None
        
        # Extract thinking from response
        separate_reasoning = None
        message = raw_response.choices[0].message
        if hasattr(message, 'reasoning') and getattr(message, 'reasoning', None):
            separate_reasoning = getattr(message, 'reasoning')
        
        # Extract thinking using ThinkingExtractor
        from .base import ThinkingExtractor
        cleaned_content, thinking = ThinkingExtractor.extract_thinking(content, separate_reasoning)

        return ParsedResponse(
            content=cleaned_content,
            tokens_used=tokens_used,
            model=raw_response.model,
            thinking=thinking,
            metadata={
                "finish_reason": raw_response.choices[0].finish_reason,
                "prompt_tokens": (
                    raw_response.usage.prompt_tokens if raw_response.usage else None
                ),
                "completion_tokens": (
                    raw_response.usage.completion_tokens if raw_response.usage else None
                ),
            },
        )
