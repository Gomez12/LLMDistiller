"""LLM Provider Manager for coordinating multiple LLM providers."""

import asyncio
import logging
import random
import traceback
from typing import Dict, List, Optional, Type

from llm_distiller.config import ProviderConfig, Settings
from llm_distiller.llm.base import BaseLLMProvider
from llm_distiller.llm.openai_provider import OpenAIProvider
from llm_distiller.utils.rate_limiter import RateLimiter

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
        logger.info(f"[DEBUG] Initializing {len(self.settings.llm_providers)} providers")
        
        for name, config in self.settings.llm_providers.items():
            try:
                logger.debug(f"[DEBUG] Initializing provider '{name}' of type '{config.type}'")
                logger.debug(f"[DEBUG] Provider config: {config}")
                
                provider_class = self.provider_classes.get(config.type)
                if not provider_class:
                    logger.error(f"[ERROR] Unknown provider type '{config.type}' for provider '{name}'")
                    raise ValueError(f"Unknown provider type: {config.type}")
                
                # Initialize provider
                provider = provider_class(config)
                self.providers[name] = provider
                logger.info(f"[DEBUG] Successfully initialized provider '{name}' with model '{provider.model_name}'")
                
                # Initialize rate limiter
                rate_limiter = RateLimiter(config.rate_limit, name)
                self.rate_limiters[name] = rate_limiter
                logger.debug(f"[DEBUG] Initialized rate limiter for provider '{name}': {config.rate_limit}")
                
            except Exception as e:
                logger.error(f"[ERROR] Failed to initialize provider '{name}': {e}")
                logger.error(f"[ERROR] Exception type: {type(e).__name__}")
                logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
                logger.error(f"[ERROR] Provider config: {config}")
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
    
    def _get_providers_for_strategy(self, strategy: str, preferred_provider: Optional[str]) -> List[str]:
        """Get list of providers to try based on failover strategy.
        
        Args:
            strategy: Failover strategy
            preferred_provider: Preferred provider name
            
        Returns:
            List of provider names in order to try
        """
        providers_to_try = []
        
        if strategy == "none":
            # Only use preferred provider if specified
            if preferred_provider and preferred_provider in self.providers:
                providers_to_try.append(preferred_provider)
        elif strategy == "preferred_only":
            # Only use preferred provider, or all if none specified
            if preferred_provider and preferred_provider in self.providers:
                providers_to_try.append(preferred_provider)
            else:
                providers_to_try = list(self.providers.keys())
        elif strategy == "rate_limit_only":
            # Try preferred provider first, then others for rate limit errors only
            if preferred_provider and preferred_provider in self.providers:
                providers_to_try.append(preferred_provider)
            # Add other providers as potential failovers
            for provider_name in self.providers:
                if provider_name not in providers_to_try:
                    providers_to_try.append(provider_name)
        elif strategy == "all":
            # Current behavior: try preferred first, then all others
            if preferred_provider and preferred_provider in self.providers:
                providers_to_try.append(preferred_provider)
            for provider_name in self.providers:
                if provider_name not in providers_to_try:
                    providers_to_try.append(provider_name)
        else:
            logger.warning(f"[WARNING] Unknown failover strategy '{strategy}', defaulting to 'none'")
            return self._get_providers_for_strategy("none", preferred_provider)
        
        return providers_to_try
    
    def _should_failover(self, strategy: str, error_type: str, attempt: int, total_attempts: int) -> bool:
        """Determine if failover should continue based on strategy and error type.
        
        Args:
            strategy: Current failover strategy
            error_type: Type of error that occurred
            attempt: Current attempt number (0-based)
            total_attempts: Total number of providers to try
            
        Returns:
            True if failover should continue, False otherwise
        """
        # If this is the last provider, no failover possible
        if attempt >= total_attempts - 1:
            return False
        
        if strategy == "none":
            # Never failover
            return False
        elif strategy == "preferred_only":
            # Never failover from preferred provider
            return False
        elif strategy == "rate_limit_only":
            # Only failover on rate limit errors
            return error_type in self.settings.processing.failover_on_errors
        elif strategy == "all":
            # Always failover
            return True
        else:
            return False
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for failover decisions.
        
        Args:
            error: Exception to classify
            
        Returns:
            Error type string: 'rate_limit', 'timeout', 'auth', 'general'
        """
        error_msg = str(error).lower()
        
        if "rate limit" in error_msg or "too many requests" in error_msg or "rate_limit" in error_msg:
            return "rate_limit"
        elif "timeout" in error_msg or "connection" in error_msg or "network" in error_msg:
            return "timeout"
        elif "authentication" in error_msg or "unauthorized" in error_msg or "forbidden" in error_msg or "api key" in error_msg:
            return "auth"
        else:
            return "general"
    
    async def generate_response_with_failover(
        self, 
        prompt: str, 
        preferred_provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        failover_strategy: Optional[str] = None
    ) -> WorkerResult:
        """Generate response with configurable failover.
        
        Args:
            prompt: Input prompt for the LLM
            preferred_provider: Preferred provider to use first
            system_prompt: Optional system prompt
            failover_strategy: Override failover strategy for this request
            
        Returns:
            WorkerResult with response or error details
        """
        # Determine strategy (CLI override > config > default)
        strategy = failover_strategy or self.settings.processing.failover_strategy
        
        logger.debug(f"[DEBUG] Starting response generation with failover strategy: {strategy}")
        logger.debug(f"[DEBUG] System prompt: {system_prompt[:100] if system_prompt else 'None'}")
        logger.debug(f"[DEBUG] Prompt (first 200 chars): {prompt[:200]}")
        logger.debug(f"[DEBUG] Preferred provider: {preferred_provider}")
        logger.debug(f"[DEBUG] Available providers: {list(self.providers.keys())}")
        
        # Determine providers to try based on strategy
        providers_to_try = self._get_providers_for_strategy(strategy, preferred_provider)
        
        if not providers_to_try:
            logger.error(f"[ERROR] No providers available for strategy '{strategy}' with preferred provider '{preferred_provider}'")
            return WorkerResult(
                question_id=0,
                provider_name=preferred_provider or "unknown",
                model_name="unknown",
                success=False,
                error_message=f"No providers available for strategy '{strategy}'",
                error_type="configuration_error"
            )
        
        logger.debug(f"[DEBUG] Provider try order: {providers_to_try}")
        
        last_error = None
        last_error_type = None
        
        for i, provider_name in enumerate(providers_to_try):
            provider = self.providers[provider_name]
            rate_limiter = self.rate_limiters.get(provider_name)
            
            logger.debug(f"[DEBUG] Attempting provider {i+1}/{len(providers_to_try)}: {provider_name}")
            logger.debug(f"[DEBUG] Provider model: {provider.model_name}")
            
            try:
                # Apply rate limiting
                if rate_limiter:
                    logger.debug(f"[DEBUG] Checking rate limits for provider '{provider_name}'")
                    await rate_limiter.acquire()
                    logger.debug(f"[DEBUG] Rate limit check passed for provider '{provider_name}'")
                
                # Combine system prompt with user prompt if provided
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                    logger.debug(f"[DEBUG] Combined prompt with system prompt")
                
                # Generate response
                logger.debug(f"[DEBUG] Calling generate_response on provider '{provider_name}'")
                logger.debug(f"[DEBUG] Generation params: {self.settings.processing.generation_params}")
                
                response = await provider.generate_response(
                    full_prompt, 
                    self.settings.processing.generation_params
                )
                
                logger.info(f"Successfully generated response using provider: {provider_name} (model: {response.model or provider.model_name})")
                logger.debug(f"[DEBUG] Response content (first 200 chars): {response.content[:200] if response.content else 'None'}")
                logger.debug(f"[DEBUG] Response tokens: {response.tokens_used}")
                logger.debug(f"[DEBUG] Response metadata: {response.metadata}")
                
                return WorkerResult(
                    question_id=0,  # Will be set by caller
                    provider_name=provider_name,
                    model_name=response.model or provider.model_name,
                    success=True,
                    response_text=response.content,
                    thinking=response.thinking,
                    tokens_used=response.tokens_used,
                    processing_time_ms=response.metadata.get("processing_time_ms"),
                )
                
            except Exception as e:
                last_error = str(e)
                last_error_type = self._classify_error(e)
                
                logger.error(f"[ERROR] Provider {provider_name} failed (attempt {i+1}/{len(providers_to_try)})")
                logger.error(f"[ERROR] Exception type: {type(e).__name__}")
                logger.error(f"[ERROR] Classified error type: {last_error_type}")
                logger.error(f"[ERROR] Exception message: {str(e)}")
                logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
                logger.error(f"[ERROR] Provider config: {provider.config if hasattr(provider, 'config') else 'N/A'}")
                logger.error(f"[ERROR] Prompt used: {prompt}")
                logger.error(f"[ERROR] Generation params: {self.settings.processing.generation_params}")
                
                # Check if we should continue with failover based on strategy and error type
                if not self._should_failover(strategy, last_error_type, i, len(providers_to_try)):
                    logger.info(f"[INFO] Failover not allowed for strategy '{strategy}' with error type '{last_error_type}'")
                    break
        
        # All providers failed or failover was stopped
        logger.error(f"[DEBUG] All {len(providers_to_try)} providers failed or failover stopped")
        logger.error(f"[DEBUG] Providers attempted: {providers_to_try}")
        logger.error(f"[DEBUG] Last error: {last_error or 'All providers failed'}")
        logger.error(f"[DEBUG] Last error type: {last_error_type}")
        logger.error(f"[DEBUG] Prompt that caused failure: {prompt}")
        
        return WorkerResult(
            question_id=0,  # Will be set by caller
            provider_name=preferred_provider or "unknown",
            model_name="unknown",
            success=False,
            error_message=last_error or "All providers failed",
            error_type=last_error_type or "provider_error"
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