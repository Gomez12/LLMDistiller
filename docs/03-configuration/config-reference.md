# Configuration Reference

Dit document beschrijft het complete configuratie systeem van de LLM Distiller, inclusief alle opties, validatie en voorbeelden.

## 📋 Overzicht

Het configuratie systeem ondersteunt:
- **JSON formaat**: Human-readable en version control friendly
- **Environment variable fallback**: Sensitive data uit environment variables
- **Validation**: Automatische validatie van configuratie
- **Flexibiliteit**: Ondersteuning voor diverse providers en settings

## 🏗️ Configuratie Structuur

### Hoofdconfiguratie
```json
{
  "database": {
    "url": "sqlite:///llm_distiller.db",
    "echo": false,
    "pool_size": 5,
    "max_overflow": 10
  },
  "llm_providers": {
    "openai_main": {
      "type": "openai",
      "api_key": "",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_minute": 90000
      },
      "default": true
    }
  },
  "default_provider": "openai_main",
  "processing": {
    "batch_size": 10,
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30.0
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/llm_distiller.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## 🗄️ Database Configuratie

### Database Settings
```json
{
  "database": {
    "url": "sqlite:///llm_distiller.db",
    "echo": false,
    "pool_size": 5,
    "max_overflow": 10,
    "connect_timeout": 30,
    "recycle": 3600
  }
}
```

#### Veld Beschrijvingen

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `url` | string | `"sqlite:///llm_distiller.db"` | Database connection URL |
| `echo` | boolean | `false` | SQL query logging |
| `pool_size` | integer | `5` | Connection pool size |
| `max_overflow` | integer | `10` | Max overflow connections |
| `connect_timeout` | integer | `30` | Connection timeout (seconds) |
| `recycle` | integer | `3600` | Connection recycle time (seconds) |

#### Database URL Voorbeelden

**SQLite:**
```json
{
  "url": "sqlite:///llm_distiller.db"
}
```

**PostgreSQL:**
```json
{
  "url": "postgresql://user:password@localhost:5432/llm_distiller"
}
```

**MySQL:**
```json
{
  "url": "mysql://user:password@localhost:3306/llm_distiller"
}
```

**SQL Server:**
```json
{
  "url": "mssql://user:password@localhost:1433/llm_distiller"
}
```

## 🤖 LLM Provider Configuratie

### OpenAI Provider
```json
{
  "openai_main": {
    "type": "openai",
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "rate_limit": {
      "requests_per_minute": 60,
      "tokens_per_minute": 90000
    },
    "default": true
  }
}
```

#### OpenAI Provider Velden

| Veld | Type | Required | Beschrijving |
|------|------|----------|-------------|
| `type` | string | Ja | Provider type (`"openai"`) |
| `api_key` | string | Nee | API key (leeg = environment variable) |
| `base_url` | string | Nee | API base URL |
| `model` | string | Nee | Default model naam |
| `rate_limit` | object | Nee | Rate limiting configuratie |
| `default` | boolean | Nee | Gebruik als default provider |

#### Environment Variables
```bash
# Voor provider "openai_main"
OPENAI_MAIN_API_KEY=sk-your-api-key-here

# Voor provider "azure_openai"
AZURE_OPENAI_API_KEY=your-azure-api-key
```

### Azure OpenAI Provider
```json
{
  "azure_openai": {
    "type": "azure_openai",
    "api_key": "",
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_version": "2023-12-01-preview",
    "deployment_name": "gpt-4",
    "rate_limit": {
      "requests_per_minute": 30,
      "tokens_per_minute": 120000
    }
  }
}
```

#### Azure OpenAI Specifieke Velden

| Veld | Type | Required | Beschrijving |
|------|------|----------|-------------|
| `type` | string | Ja | Provider type (`"azure_openai"`) |
| `api_key` | string | Ja | Azure OpenAI API key |
| `endpoint` | string | Ja | Azure OpenAI endpoint |
| `api_version` | string | Nee | API version |
| `deployment_name` | string | Ja | Deployment naam |

### Local Ollama Provider
```json
{
  "local_ollama": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2",
    "rate_limit": {
      "requests_per_minute": 1000,
      "tokens_per_minute": 1000000
    }
  }
}
```

### Custom OpenAI-Compatible Provider
```json
{
  "custom_provider": {
    "type": "openai",
    "api_key": "your-custom-key",
    "base_url": "https://your-custom-endpoint.com/v1",
    "model": "custom-model",
    "rate_limit": {
      "requests_per_minute": 100,
      "tokens_per_minute": 50000
    },
    "headers": {
      "Custom-Header": "value"
    }
  }
}
```

## ⚙️ Rate Limiting Configuratie

### Rate Limit Settings
```json
{
  "rate_limit": {
    "requests_per_minute": 60,
    "tokens_per_minute": 90000,
    "burst_size": 10,
    "retry_after_base": 1.0,
    "retry_after_max": 60.0,
    "adaptive": true
  }
}
```

#### Rate Limit Velden

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `requests_per_minute` | integer | `60` | Max requests per minuut |
| `tokens_per_minute` | integer | `90000` | Max tokens per minuut |
| `burst_size` | integer | `10` | Burst capacity |
| `retry_after_base` | float | `1.0` | Base retry wait time |
| `retry_after_max` | float | `60.0` | Maximum retry wait time |
| `adaptive` | boolean | `true` | Adaptive rate limiting |

### Provider-Specific Limits

**OpenAI (Free Tier):**
```json
{
  "rate_limit": {
    "requests_per_minute": 3,
    "tokens_per_minute": 40000
  }
}
```

**OpenAI (Paid Tier):**
```json
{
  "rate_limit": {
    "requests_per_minute": 3500,
    "tokens_per_minute": 90000
  }
}
```

**Azure OpenAI:**
```json
{
  "rate_limit": {
    "requests_per_minute": 300,
    "tokens_per_minute": 120000
  }
}
```

## 🔄 Processing Configuratie

### Processing Settings
```json
{
  "processing": {
    "batch_size": 10,
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "concurrent_requests": 5,
    "progress_interval": 10,
    "save_interval": 100
  }
}
```

#### Processing Velden

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `batch_size` | integer | `10` | Batch size voor processing |
| `max_retries` | integer | `3` | Maximum retry attempts |
| `retry_delay` | float | `1.0` | Base retry delay (seconds) |
| `timeout` | float | `30.0` | Request timeout (seconds) |
| `concurrent_requests` | integer | `5` | Concurrent API requests |
| `progress_interval` | integer | `10` | Progress report interval |
| `save_interval` | integer | `100` | Database save interval |

### Performance Tuning

**High Performance:**
```json
{
  "processing": {
    "batch_size": 50,
    "concurrent_requests": 20,
    "timeout": 60.0
  }
}
```

**Resource Constrained:**
```json
{
  "processing": {
    "batch_size": 5,
    "concurrent_requests": 2,
    "timeout": 30.0
  }
}
```

## 📝 Logging Configuratie

### Logging Settings
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/llm_distiller.log",
    "max_size": "10MB",
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "console": true,
    "console_level": "INFO"
  }
}
```

#### Logging Velden

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `level` | string | `"DEBUG"` | Logging level |
| `file` | string | `"logs/llm_distiller.log"` | Log file path |
| `max_size` | string | `"10MB"` | Max log file size |
| `backup_count` | integer | `5` | Number of backup files |
| `format` | string | - | Log message format |
| `console` | boolean | `true` | Console logging |
| `console_level` | string | `"INFO"` | Console log level |

#### Logging Levels

**Development:**
```json
{
  "logging": {
    "level": "DEBUG",
    "console": true,
    "console_level": "DEBUG"
  }
}
```

**Production:**
```json
{
  "logging": {
    "level": "INFO",
    "console": false,
    "file": "/var/log/llm_distiller/app.log"
  }
}
```

## 🔧 Advanced Configuratie

### Validation Settings
```json
{
  "validation": {
    "strict_mode": true,
    "auto_fix": false,
    "max_error_length": 1000,
    "cache_schemas": true,
    "schema_timeout": 5.0
  }
}
```

#### Validation Velden

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `strict_mode` | boolean | `true` | Strict validation mode |
| `auto_fix` | boolean | `false` | Auto-fix common issues |
| `max_error_length` | integer | `1000` | Max error message length |
| `cache_schemas` | boolean | `true` | Cache parsed schemas |
| `schema_timeout` | float | `5.0` | Schema validation timeout |

### Export Settings
```json
{
  "export": {
    "default_format": "jsonl",
    "include_metadata": false,
    "compression": "none",
    "chunk_size": 1000,
    "max_file_size": "100MB"
  }
}
```

#### Export Velden

| Veld | Type | Default | Beschrijving |
|------|------|----------|-------------|
| `default_format` | string | `"jsonl"` | Default export format |
| `include_metadata` | boolean | `false` | Include metadata in export |
| `compression` | string | `"none"` | File compression |
| `chunk_size` | integer | `1000` | Export chunk size |
| `max_file_size` | string | `"100MB"` | Max export file size |

## 📁 Configuratie Bestanden

### Configuratie Bestand Locaties

De LLM Distiller zoekt configuratie in de volgende volgorde:

1. **Command line argument**: `--config /path/to/config.json`
2. **Environment variable**: `LLM_DISTILLER_CONFIG=/path/to/config.json`
3. **Default locations**:
   - `./config/config.json`
   - `~/.config/llm_distiller/config.json`
   - `/etc/llm_distiller/config.json`

### Configuratie Template

**config/config.json.example:**
```json
{
  "database": {
    "url": "sqlite:///llm_distiller.db",
    "echo": false
  },
  "llm_providers": {
    "openai_main": {
      "type": "openai",
      "api_key": "",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 60,
        "tokens_per_minute": 90000
      },
      "default": true
    },
    "local_ollama": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://localhost:11434/v1",
      "model": "llama2",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 1000000
      }
    }
  },
  "default_provider": "openai_main",
  "processing": {
    "batch_size": 10,
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30.0
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/llm_distiller.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## 🔍 Configuratie Validatie

### Pydantic Models
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional

class DatabaseConfig(BaseModel):
    url: str = Field(default="sqlite:///llm_distiller.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    connect_timeout: int = Field(default=30, ge=1)
    recycle: int = Field(default=3600, ge=0)

class RateLimitConfig(BaseModel):
    requests_per_minute: int = Field(default=60, ge=1)
    tokens_per_minute: int = Field(default=90000, ge=1)
    burst_size: int = Field(default=10, ge=1)
    retry_after_base: float = Field(default=1.0, ge=0.1)
    retry_after_max: float = Field(default=60.0, ge=1.0)
    adaptive: bool = Field(default=True)

class ProviderConfig(BaseModel):
    type: str = Field(..., description="Provider type")
    api_key: str = Field(default="", description="API key")
    base_url: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-3.5-turbo")
    deployment_name: Optional[str] = Field(default=None)
    endpoint: Optional[str] = Field(default=None)
    api_version: str = Field(default="2023-12-01-preview")
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    default: bool = Field(default=False)
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['openai', 'azure_openai', 'custom']
        if v not in valid_types:
            raise ValueError(f"Invalid provider type: {v}")
        return v

class ProcessingConfig(BaseModel):
    batch_size: int = Field(default=10, ge=1, le=1000)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    concurrent_requests: int = Field(default=5, ge=1, le=50)
    progress_interval: int = Field(default=10, ge=1)
    save_interval: int = Field(default=100, ge=1)

class LoggingConfig(BaseModel):
    level: str = Field(default="DEBUG")
    file: str = Field(default="logs/llm_distiller.log")
    max_size: str = Field(default="10MB")
    backup_count: int = Field(default=5, ge=1)
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console: bool = Field(default=True)
    console_level: str = Field(default="INFO")
    
    @validator('level', 'console_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()

class Settings(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm_providers: Dict[str, ProviderConfig] = Field(...)
    default_provider: Optional[str] = Field(default=None)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @validator('default_provider')
    def validate_default_provider(cls, v, values):
        if v is None:
            # Find provider marked as default
            providers = values.get('llm_providers', {})
            for name, config in providers.items():
                if config.default:
                    return name
            # Return first provider as fallback
            if providers:
                return list(providers.keys())[0]
        return v
```

## 🚀 Configuratie Examples

### Development Setup
```json
{
  "database": {
    "url": "sqlite:///dev_llm_distiller.db",
    "echo": true
  },
  "llm_providers": {
    "local_ollama": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://localhost:11434/v1",
      "model": "llama2",
      "default": true
    }
  },
  "processing": {
    "batch_size": 5,
    "concurrent_requests": 2
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "console_level": "DEBUG"
  }
}
```

### Production Setup
```json
{
  "database": {
    "url": "postgresql://prod_user:secure_pass@db.example.com:5432/llm_distiller",
    "pool_size": 20,
    "max_overflow": 30
  },
  "llm_providers": {
    "openai_prod": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4",
      "rate_limit": {
        "requests_per_minute": 100,
        "tokens_per_minute": 90000
      },
      "default": true
    },
    "azure_backup": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://backup-resource.openai.azure.com/",
      "deployment_name": "gpt-4"
    }
  },
  "processing": {
    "batch_size": 50,
    "concurrent_requests": 10,
    "timeout": 60.0
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llm_distiller/app.log",
    "console": false,
    "max_size": "100MB",
    "backup_count": 10
  }
}
```

### High-Throughput Setup
```json
{
  "database": {
    "url": "postgresql://user:pass@high-perf-db:5432/llm_distiller",
    "pool_size": 50,
    "max_overflow": 100
  },
  "llm_providers": {
    "openai_high": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 3000,
        "tokens_per_minute": 90000
      }
    }
  },
  "processing": {
    "batch_size": 100,
    "concurrent_requests": 50,
    "timeout": 30.0,
    "save_interval": 500
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/llm_distiller/high-throughput.log"
  }
}
```

---

*Deze configuratie reference biedt een compleet overzicht van alle beschikbare opties en hun validatie regels voor de LLM Distiller.*