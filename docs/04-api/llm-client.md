# LLM Client

Dit document beschrijft de LLM client architectuur, provider implementaties en rate limiting systemen van de LLM Distiller.

## 📋 Overzicht

De LLM client is ontworpen voor:
- **Multi-provider support**: Ondersteuning voor diverse LLM providers
- **Rate limiting**: Intelligent rate limiting met API feedback
- **Error handling**: Robuste error handling en retry logic
- **Flexibility**: Configuratiebare parameters per provider
- **Thinking extraction**: Automatische extractie van model reasoning processen

## 🧠 Thinking Extraction

### Thinking Extraction Functionaliteit
De LLM client ondersteunt automatische extractie van thinking/reasoning uit model responses:

```python
from llm.base import ThinkingExtractor

# Extract thinking from response with tags
response = """<thinking>
Ik moet dit stap voor stap analyseren.
Eerst begrijp ik de vraag.
Dan formuleer ik een antwoord.
</thinking>

Dit is het uiteindelijke antwoord."""

cleaned_content, thinking = ThinkingExtractor.extract_thinking(response)
print(f"Cleaned: {cleaned_content}")
print(f"Thinking: {thinking}")
```

### Ondersteunde Thinking Formaten

#### 1. Thinking Tags
```xml
<thinking>
Dit is de reasoning van het model.
Het wordt automatisch geëxtraheerd.
</thinking>

Dit is het schone antwoord.
```

#### 2. Reasoning Tags
```xml
<reasoning>
Alternatieve reasoning tags worden ook ondersteund.
Deze functie is backwards compatible.
</reasoning>

Antwoord zonder reasoning tags.
```

#### 3. Separate Reasoning (Future Models)
```python
# Voor toekomstige modellen die separate reasoning teruggeven
separate_reasoning = "Dit is de separate reasoning van het model"
response_text = "Dit is het antwoord."

cleaned_content, thinking = ThinkingExtractor.extract_thinking(
    response_text, separate_reasoning
)
```

### Database Opslag
Thinking wordt opgeslagen in de `thinking` kolom van:
- `responses` tabel voor geldige responses
- `invalid_responses` tabel voor ongeldige responses

### Processing Flow
1. **Response Generation**: LLM genereert response met mogelijke thinking tags
2. **Thinking Extraction**: ThinkingExtractor haalt reasoning uit response
3. **Content Cleaning**: Thinking tags worden verwijderd uit de response content
4. **Database Storage**: Schone content en thinking worden apart opgeslagen

## 🏗️ Client Architecture

### Base Provider Interface
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import time

class ProviderType(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"

@dataclass
class GenerationConfig:
    """Configuration for LLM generation"""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_prompt: Optional[str] = None
    stop_sequences: Optional[List[str]] = None

@dataclass
class LLMResponse:
    """Standardized LLM response"""
    content: str
    reasoning: Optional[str] = None
    thinking: Optional[str] = None  # Model reasoning/thinking process
    model: str = ""
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    response_time: float = 0.0
    provider: str = ""
    raw_response: Optional[Dict[str, Any]] = None

class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.rate_limiter = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize provider-specific client"""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, config: GenerationConfig) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def get_rate_limiter(self):
        """Get provider-specific rate limiter"""
        pass
    
    async def generate_with_retry(self, prompt: str, config: GenerationConfig, 
                                max_retries: int = 3) -> LLMResponse:
        """Generate response with retry logic"""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Check rate limits
                if self.rate_limiter:
                    await self.rate_limiter.acquire(self.name)
                
                # Generate response
                start_time = time.time()
                response = await self.generate_response(prompt, config)
                response.response_time = time.time() - start_time
                response.provider = self.name
                
                # Update rate limiter with response info
                if self.rate_limiter and response.raw_response:
                    self.rate_limiter.update_from_response(response.raw_response)
                
                return response
                
            except Exception as e:
                last_error = e
                
                # Check if we should retry
                if attempt < max_retries and self._should_retry(e):
                    wait_time = self._calculate_retry_wait(attempt)
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
        
        # All retries failed
        raise last_error
    
    def _should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        # Implement retry logic based on error type
        if "rate limit" in str(error).lower():
            return True
        if "timeout" in str(error).lower():
            return True
        if "connection" in str(error).lower():
            return True
        return False
    
    def _calculate_retry_wait(self, attempt: int) -> float:
        """Calculate exponential backoff wait time"""
        base_wait = 1.0
        max_wait = 60.0
        wait_time = base_wait * (2 ** attempt)
        return min(wait_time, max_wait)
```

## 🤖 OpenAI Provider

### OpenAI Provider Implementation
```python
import openai
from openai import AsyncOpenAI
from typing import Dict, Any, Optional

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.client = None
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = self.config.get('api_key')
        base_url = self.config.get('base_url', 'https://api.openai.com/v1')
        
        if not api_key:
            raise ValueError(f"API key required for OpenAI provider: {self.name}")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Initialize rate limiter
        self.rate_limiter = self.get_rate_limiter()
    
    async def generate_response(self, prompt: str, config: GenerationConfig) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            # Prepare messages
            messages = []
            
            if config.system_prompt:
                messages.append({"role": "system", "content": config.system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences
            )
            
            # Extract response data
            choice = response.choices[0]
            content = choice.message.content
            
            # Extract reasoning if available (for models that support it)
            reasoning = None
            if hasattr(choice.message, 'reasoning_content'):
                reasoning = choice.message.reasoning_content
            
            # Extract thinking from response content
            from ..base import ThinkingExtractor
            separate_reasoning = getattr(choice.message, 'reasoning', None)
            cleaned_content, thinking = ThinkingExtractor.extract_thinking(content, separate_reasoning)
            
            return LLMResponse(
                content=cleaned_content,
                reasoning=reasoning,
                thinking=thinking,
                model=response.model,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                finish_reason=choice.finish_reason,
                provider=self.name,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else str(response)
            )
            
        except openai.RateLimitError as e:
            raise Exception(f"Rate limit exceeded: {e}")
        except openai.APIError as e:
            raise Exception(f"OpenAI API error: {e}")
        except Exception as e:
            raise Exception(f"OpenAI provider error: {e}")
    
    def get_rate_limiter(self):
        """Get OpenAI-specific rate limiter"""
        from ..rate_limiting.limiter import OpenAIRateLimiter
        return OpenAIRateLimiter(self.config.get('rate_limit', {}))
```

### Azure OpenAI Provider
```python
class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation"""
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        api_key = self.config.get('api_key')
        endpoint = self.config.get('endpoint')
        api_version = self.config.get('api_version', '2023-12-01-preview')
        
        if not api_key or not endpoint:
            raise ValueError(f"API key and endpoint required for Azure OpenAI: {self.name}")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        
        self.rate_limiter = self.get_rate_limiter()
    
    async def generate_response(self, prompt: str, config: GenerationConfig) -> LLMResponse:
        """Generate response using Azure OpenAI API"""
        try:
            # Azure OpenAI uses deployment name instead of model
            deployment_name = self.config.get('deployment_name', config.model)
            
            messages = []
            if config.system_prompt:
                messages.append({"role": "system", "content": config.system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=deployment_name,  # Azure uses deployment name
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences
            )
            
            choice = response.choices[0]
            content = choice.message.content
            
            return LLMResponse(
                content=content,
                model=deployment_name,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                },
                finish_reason=choice.finish_reason,
                provider=self.name,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else str(response)
            )
            
        except Exception as e:
            raise Exception(f"Azure OpenAI provider error: {e}")
    
    def get_rate_limiter(self):
        """Get Azure OpenAI rate limiter"""
        from ..rate_limiting.limiter import AzureRateLimiter
        return AzureRateLimiter(self.config.get('rate_limit', {}))
```

## 🎛️ Provider Manager

### Provider Manager Implementation
```python
from typing import Dict, List, Optional
import logging

class LLMProviderManager:
    """Manages multiple LLM providers with failover support"""
    
    def __init__(self, providers_config: Dict[str, Dict[str, Any]]):
        self.providers = {}
        self.default_provider = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize providers
        for name, config in providers_config.items():
            try:
                provider = self._create_provider(name, config)
                self.providers[name] = provider
                
                # Set default provider
                if not self.default_provider or config.get('default', False):
                    self.default_provider = name
                    
            except Exception as e:
                self.logger.error(f"Failed to initialize provider {name}: {e}")
    
    def _create_provider(self, name: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """Create provider instance based on type"""
        provider_type = config.get('type', 'openai')
        
        if provider_type == 'openai':
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(name, config)
        elif provider_type == 'azure_openai':
            from .azure_openai_provider import AzureOpenAIProvider
            return AzureOpenAIProvider(name, config)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    async def generate_response(self, prompt: str, config: GenerationConfig, 
                                provider_name: Optional[str] = None) -> LLMResponse:
        """Generate response using specified or default provider"""
        provider_name = provider_name or self.default_provider
        
        if not provider_name:
            raise ValueError("No provider specified and no default provider available")
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider not found: {provider_name}")
        
        provider = self.providers[provider_name]
        return await provider.generate_with_retry(prompt, config)
    
    async def generate_with_failover(self, prompt: str, config: GenerationConfig,
                                   provider_order: Optional[List[str]] = None) -> LLMResponse:
        """Generate response with provider failover"""
        providers_to_try = provider_order or list(self.providers.keys())
        last_error = None
        
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            try:
                self.logger.info(f"Trying provider: {provider_name}")
                return await self.generate_response(prompt, config, provider_name)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Get provider by name"""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all available providers"""
        return list(self.providers.keys())
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                'type': provider.config.get('type'),
                'model': provider.config.get('model'),
                'rate_limiter': provider.rate_limiter is not None,
                'available': True  # Could implement health check
            }
        return status
```

## 🚦 Rate Limiting System

### Base Rate Limiter
```python
import asyncio
import time
from collections import deque, defaultdict
from typing import Dict, Optional

class BaseRateLimiter:
    """Base rate limiter with adaptive capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.requests_per_minute = config.get('requests_per_minute', 60)
        self.tokens_per_minute = config.get('tokens_per_minute', 90000)
        
        # Request tracking
        self.request_history = deque()
        self.token_history = deque()
        
        # API-adaptive limits
        self.api_requests_per_minute = None
        self.api_tokens_per_minute = None
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def acquire(self, provider_name: str) -> bool:
        """Acquire permission to make request"""
        async with self._lock:
            now = time.time()
            window_start = now - 60  # 1 minute window
            
            # Clean old requests
            while self.request_history and self.request_history[0] < window_start:
                self.request_history.popleft()
            
            while self.token_history and self.token_history[0] < window_start:
                self.token_history.popleft()
            
            # Check limits
            current_requests = len(self.request_history)
            current_tokens = sum(self.token_history)
            
            # Use the most restrictive limit
            max_requests = min(
                self.requests_per_minute,
                self.api_requests_per_minute or float('inf')
            )
            max_tokens = min(
                self.tokens_per_minute,
                self.api_tokens_per_minute or float('inf')
            )
            
            if current_requests >= max_requests:
                wait_time = 60 - (now - self.request_history[0])
                await asyncio.sleep(wait_time)
                return await self.acquire(provider_name)
            
            if current_tokens >= max_tokens:
                wait_time = 60 - (now - self.token_history[0])
                await asyncio.sleep(wait_time)
                return await self.acquire(provider_name)
            
            # Record request
            self.request_history.append(now)
            return True
    
    def record_token_usage(self, tokens: int):
        """Record token usage for rate limiting"""
        self.token_history.append(tokens)
    
    def update_from_response(self, response_headers: Dict[str, Any]):
        """Update limits based on API response headers"""
        # Implementation depends on provider
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        now = time.time()
        window_start = now - 60
        
        recent_requests = sum(1 for t in self.request_history if t >= window_start)
        recent_tokens = sum(t for t in self.token_history if t >= window_start)
        
        return {
            'requests_per_minute': recent_requests,
            'tokens_per_minute': recent_tokens,
            'max_requests_per_minute': self.requests_per_minute,
            'max_tokens_per_minute': self.tokens_per_minute,
            'api_requests_per_minute': self.api_requests_per_minute,
            'api_tokens_per_minute': self.api_tokens_per_minute
        }
```

### OpenAI Rate Limiter
```python
class OpenAIRateLimiter(BaseRateLimiter):
    """OpenAI-specific rate limiter with API feedback"""
    
    def update_from_response(self, response_headers: Dict[str, Any]):
        """Update limits based on OpenAI response headers"""
        # OpenAI provides rate limit headers
        if 'x-ratelimit-limit-requests' in response_headers:
            self.api_requests_per_minute = int(response_headers['x-ratelimit-limit-requests'])
        
        if 'x-ratelimit-limit-tokens' in response_headers:
            self.api_tokens_per_minute = int(response_headers['x-ratelimit-limit-tokens'])
        
        # Handle rate limit errors
        if 'x-ratelimit-reset-requests' in response_headers:
            reset_time = int(response_headers['x-ratelimit-reset-requests'])
            wait_time = max(0, reset_time - time.time())
            # Could implement more sophisticated waiting logic here
    
    def get_retry_after(self, error_response: Dict[str, Any]) -> Optional[float]:
        """Extract retry-after time from error response"""
        # OpenAI rate limit errors include retry_after
        if isinstance(error_response, dict):
            error = error_response.get('error', {})
            if error.get('type') == 'rate_limit_exceeded':
                return error.get('retry_after', 60)
        return None
```

### Azure Rate Limiter
```python
class AzureRateLimiter(BaseRateLimiter):
    """Azure OpenAI-specific rate limiter"""
    
    def update_from_response(self, response_headers: Dict[str, Any]):
        """Update limits based on Azure response headers"""
        # Azure has different rate limit headers
        if 'x-ratelimit-remaining-requests' in response_headers:
            remaining = int(response_headers['x-ratelimit-remaining-requests'])
            # Could adjust behavior based on remaining quota
        
        if 'x-ratelimit-remaining-tokens' in response_headers:
            remaining = int(response_headers['x-ratelimit-remaining-tokens'])
            # Could implement token-aware throttling
```

## 🔧 Configuration Integration

### Provider Configuration
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = Field(default=60, ge=1)
    tokens_per_minute: int = Field(default=90000, ge=1)

class ProviderConfig(BaseModel):
    """Provider configuration"""
    type: str = Field(description="Provider type")
    api_key: str = Field(default="", description="API key (empty = use environment)")
    base_url: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-3.5-turbo")
    deployment_name: Optional[str] = Field(default=None, description="Azure deployment name")
    endpoint: Optional[str] = Field(default=None, description="Azure endpoint")
    api_version: Optional[str] = Field(default="2023-12-01-preview", description="Azure API version")
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    default: bool = Field(default=False, description="Use as default provider")
    
    def get_api_key(self) -> str:
        """Get API key from config or environment"""
        if self.api_key:
            return self.api_key
        
        # Try environment variable
        env_var = f"{self.type.upper()}_API_KEY"
        if self.type == "azure_openai":
            env_var = "AZURE_OPENAI_API_KEY"
        
        import os
        return os.getenv(env_var, "")
    
    class Config:
        extra = "allow"  # Allow additional fields for custom providers

class LLMConfig(BaseModel):
    """LLM configuration"""
    providers: Dict[str, ProviderConfig] = Field(description="Provider configurations")
    default_provider: Optional[str] = Field(default=None, description="Default provider name")
    processing: Dict[str, Any] = Field(default_factory=dict, description="Processing settings")
    
    def get_default_provider(self) -> Optional[str]:
        """Get default provider name"""
        if self.default_provider:
            return self.default_provider
        
        # Find provider marked as default
        for name, config in self.providers.items():
            if config.default:
                return name
        
        # Return first provider as fallback
        if self.providers:
            return list(self.providers.keys())[0]
        
        return None
```

## 📊 Usage Examples

### Basic Usage
```python
# Initialize provider manager
providers_config = {
    "openai_main": {
        "type": "openai",
        "api_key": "your-api-key",
        "model": "gpt-4",
        "rate_limit": {
            "requests_per_minute": 60,
            "tokens_per_minute": 90000
        }
    },
    "local_ollama": {
        "type": "openai",
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
        "model": "llama2"
    }
}

manager = LLMProviderManager(providers_config)

# Generate response
config = GenerationConfig(
    model="gpt-4",
    temperature=0.1,
    max_tokens=500
)

response = await manager.generate_response(
    prompt="What is 2+2?",
    config=config
)

print(f"Response: {response.content}")
print(f"Tokens used: {response.usage}")
```

### Failover Usage
```python
# Try multiple providers in order
response = await manager.generate_with_failover(
    prompt="Explain quantum computing",
    config=config,
    provider_order=["openai_main", "local_ollama"]
)
```

### Batch Processing
```python
async def process_questions(questions: List[str], manager: LLMProviderManager):
    """Process multiple questions concurrently"""
    tasks = []
    
    for question in questions:
        task = manager.generate_response(question, config)
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, response in enumerate(responses):
        if isinstance(response, Exception):
            print(f"Question {i} failed: {response}")
        else:
            print(f"Question {i} answered: {response.content[:100]}...")
```

---

*Deze LLM client architectuur biedt een robuuste, flexibele basis voor het integreren van diverse LLM providers met intelligent rate limiting en error handling.*