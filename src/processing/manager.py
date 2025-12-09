"""LLM Provider Manager for coordinating multiple LLM providers."""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Type

from ..config import ProviderConfig, Settings
from ..llm.base import BaseLLMProvider
from ..llm.openai_provider import OpenAIProvider
from ..utils.rate_limiter import RateLimiter
from .models import WorkerResult

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """Manages multiple LLM providers with failover and load balancing."""
    
    def __init__(self, settings: Settings):
        """Initialize the provider manager.
        
        Args:
            settings: Application settings containing provider configurations
        """
        self.settings = settings
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.provider_classes: Dict[str, Type[BaseLLMProvider]] = {
            "openai": OpenAIProvider,
            # Add other providers as they're implemented
        }
        
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        for name, config in self.settings.llm_providers.items():
            try:
                provider_class = self.provider_classes.get(config.type)
                if not provider_class:
                    raise ValueError(f"Unknown provider type: {config.type}")
                
                # Initialize provider
                provider = provider_class(config)
                self.providers[name] = provider
                
                # Initialize rate limiter
                rate_limiter = RateLimiter(config.rate_limit, name)
                self.rate_limiters[name] = rate_limiter
                
            except Exception as e:
                print(f"Failed to initialize provider '{name}': {e}")
                continue
    
    def get_provider(self, name: Optional[str] = None) -> Optional[BaseLLMProvider]:
        """Get a provider by name, or a random available provider.
        
        Args:
            name: Specific provider name, or None for random selection
            
        Returns:
            Provider instance or None if not available
        """
        if name and name in self.providers:
            return self.providers[name]
        
        if not self.providers:
            return None
        
        # Return random provider for load balancing
        return random.choice(list(self.providers.values()))
    
    def get_rate_limiter(self, provider_name: str) -> Optional[RateLimiter]:
        """Get rate limiter for a specific provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Rate limiter instance or None if not found
        """
        return self.rate_limiters.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self.providers.keys())
    
    def get_provider_for_model(self, model_name: str) -> Optional[BaseLLMProvider]:
        """Get provider that supports the specified model.
        
        Args:
            model_name: Model name to find provider for
            
        Returns:
            Provider instance or None if not found
        """
        for provider in self.providers.values():
            if provider.model_name == model_name:
                return provider
        return None
    
    async def generate_response_with_failover(
        self, 
        prompt: str, 
        preferred_provider: Optional[str] = None
    ) -> WorkerResult:
        """Generate response with automatic failover.
        
        Args:
            prompt: Input prompt for the LLM
            preferred_provider: Preferred provider to use first
            
        Returns:
            WorkerResult with response or error details
        """
        providers_to_try = []
        
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        # Add other providers for failover
        for provider_name in self.providers:
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)
        
        last_error = None
        
        for provider_name in providers_to_try:
            provider = self.providers[provider_name]
            rate_limiter = self.rate_limiters.get(provider_name)
            
            try:
                # Apply rate limiting
                if rate_limiter:
                    await rate_limiter.acquire()
                
                # Generate response
                response = await provider.generate_response(
                    prompt, 
                    self.settings.processing.generation_params
                )
                
                logger.info(f"Successfully generated response using provider: {provider_name} (model: {response.model or provider.model_name})")
                
                return WorkerResult(
                    question_id=0,  # Will be set by caller
                    provider_name=provider_name,
                    model_name=response.model or provider.model_name,
                    success=True,
                    response_text=response.content,
                    tokens_used=response.tokens_used,
                    processing_time_ms=response.metadata.get("processing_time_ms"),
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # All providers failed
        logger.error(f"All providers failed. Last error: {last_error or 'All providers failed'}")
        return WorkerResult(
            question_id=0,  # Will be set by caller
            provider_name=preferred_provider or "unknown",
            model_name="unknown",
            success=False,
            error_message=last_error or "All providers failed",
            error_type="provider_error"
        )
    
    def add_provider(self, name: str, config: ProviderConfig) -> bool:
        """Add a new provider at runtime.
        
        Args:
            name: Provider name
            config: Provider configuration
            
        Returns:
            True if provider was added successfully
        """
        try:
            provider_class = self.provider_classes.get(config.type)
            if not provider_class:
                return False
            
            provider = provider_class(config)
            self.providers[name] = provider
            
            rate_limiter = RateLimiter(config.rate_limit, name)
            self.rate_limiters[name] = rate_limiter
            
            return True
            
        except Exception:
            return False
    
    def remove_provider(self, name: str) -> bool:
        """Remove a provider.
        
        Args:
            name: Provider name to remove
            
        Returns:
            True if provider was removed
        """
        if name in self.providers:
            del self.providers[name]
        if name in self.rate_limiters:
            del self.rate_limiters[name]
        return name in self.providers
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """Get statistics for all providers."""
        stats = {}
        for name, provider in self.providers.items():
            rate_limiter = self.rate_limiters.get(name)
            stats[name] = {
                "type": provider.provider_name,
                "model": provider.model_name,
                "rate_limiter": {
                    "active": rate_limiter is not None,
                    "requests_per_minute": rate_limiter.config.requests_per_minute if rate_limiter else None,
                    "requests_per_hour": rate_limiter.config.requests_per_hour if rate_limiter else None,
                } if rate_limiter else None
            }
        return stats