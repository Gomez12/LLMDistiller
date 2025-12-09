# LLM Provider Configuration

Dit document beschrijft de configuratie van verschillende LLM providers, inclusief specifieke settings, rate limiting en best practices.

## 📋 Overzicht

De LLM Distiller ondersteunt diverse providers:
- **OpenAI**: Officiële OpenAI API
- **Azure OpenAI**: Microsoft's OpenAI offering
- **Local Ollama**: Lokale modellen via Ollama
- **Custom**: Elke OpenAI-compatible endpoint

## 🤖 OpenAI Provider

### Basis Configuratie
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

### OpenAI Modellen

#### GPT-4 Series
```json
{
  "gpt4_turbo": {
    "type": "openai",
    "model": "gpt-4-turbo-preview",
    "rate_limit": {
      "requests_per_minute": 500,
      "tokens_per_minute": 300000
    }
  },
  "gpt4_vision": {
    "type": "openai",
    "model": "gpt-4-vision-preview",
    "rate_limit": {
      "requests_per_minute": 200,
      "tokens_per_minute": 200000
    }
  }
}
```

#### GPT-3.5 Series
```json
{
  "gpt35_turbo": {
    "type": "openai",
    "model": "gpt-3.5-turbo",
    "rate_limit": {
      "requests_per_minute": 3500,
      "tokens_per_minute": 90000
    }
  },
  "gpt35_instruct": {
    "type": "openai",
    "model": "gpt-3.5-turbo-instruct",
    "rate_limit": {
      "requests_per_minute": 3500,
      "tokens_per_minute": 90000
    }
  }
}
```

### OpenAI Rate Limits

#### Free Tier Limits
```json
{
  "openai_free": {
    "type": "openai",
    "rate_limit": {
      "requests_per_minute": 3,
      "tokens_per_minute": 40000
    }
  }
}
```

#### Pay-as-you-go Tier Limits
```json
{
  "openai_paid": {
    "type": "openai",
    "rate_limit": {
      "requests_per_minute": 3500,
      "tokens_per_minute": 90000
    }
  }
}
```

#### Tier-Specific Limits
| Tier | Requests/Min | Tokens/Min | Models |
|------|--------------|------------|--------|
| Free | 3 | 40,000 | GPT-3.5 |
| Pay-as-you-go | 3,500 | 90,000 | GPT-3.5 |
| Pay-as-you-go | 500 | 300,000 | GPT-4 |
| Pay-as-you-go | 200 | 200,000 | GPT-4 Vision |

### OpenAI Best Practices

#### Cost Optimization
```json
{
  "openai_optimized": {
    "type": "openai",
    "model": "gpt-3.5-turbo",
    "rate_limit": {
      "requests_per_minute": 1000,
      "tokens_per_minute": 50000
    },
    "generation_params": {
      "max_tokens": 500,
      "temperature": 0.1
    }
  }
}
```

#### Quality vs Speed Trade-offs
```json
{
  "openai_quality": {
    "type": "openai",
    "model": "gpt-4-turbo-preview",
    "generation_params": {
      "temperature": 0.1,
      "max_tokens": 2000,
      "top_p": 0.95
    }
  },
  "openai_speed": {
    "type": "openai",
    "model": "gpt-3.5-turbo",
    "generation_params": {
      "temperature": 0.3,
      "max_tokens": 300,
      "top_p": 0.9
    }
  }
}
```

## ☁️ Azure OpenAI Provider

### Basis Configuratie
```json
{
  "azure_openai": {
    "type": "azure_openai",
    "api_key": "",
    "endpoint": "https://your-resource.openai.azure.com/",
    "api_version": "2023-12-01-preview",
    "deployment_name": "gpt-4",
    "rate_limit": {
      "requests_per_minute": 300,
      "tokens_per_minute": 120000
    }
  }
}
```

### Azure OpenAI Modellen

#### GPT-4 Deployments
```json
{
  "azure_gpt4": {
    "type": "azure_openai",
    "endpoint": "https://gpt4-resource.openai.azure.com/",
    "deployment_name": "gpt-4",
    "rate_limit": {
      "requests_per_minute": 300,
      "tokens_per_minute": 120000
    }
  },
  "azure_gpt4_32k": {
    "type": "azure_openai",
    "endpoint": "https://gpt4-resource.openai.azure.com/",
    "deployment_name": "gpt-4-32k",
    "rate_limit": {
      "requests_per_minute": 100,
      "tokens_per_minute": 150000
    }
  }
}
```

#### GPT-3.5 Deployments
```json
{
  "azure_gpt35": {
    "type": "azure_openai",
    "endpoint": "https://gpt35-resource.openai.azure.com/",
    "deployment_name": "gpt-35-turbo",
    "rate_limit": {
      "requests_per_minute": 300,
      "tokens_per_minute": 120000
    }
  }
}
```

### Azure OpenAI Rate Limits

#### Standard PTU (Provisioned Throughput Units)
```json
{
  "azure_ptu_100": {
    "type": "azure_openai",
    "rate_limit": {
      "requests_per_minute": 1000,
      "tokens_per_minute": 300000
    }
  },
  "azure_ptu_200": {
    "type": "azure_openai",
    "rate_limit": {
      "requests_per_minute": 2000,
      "tokens_per_minute": 600000
    }
  }
}
```

#### Pay-as-you-go Limits
```json
{
  "azure_payg": {
    "type": "azure_openai",
    "rate_limit": {
      "requests_per_minute": 300,
      "tokens_per_minute": 120000
    }
  }
}
```

### Azure OpenAI Best Practices

#### Multi-Region Setup
```json
{
  "azure_east_us": {
    "type": "azure_openai",
    "endpoint": "https://east-us-resource.openai.azure.com/",
    "deployment_name": "gpt-4"
  },
  "azure_west_europe": {
    "type": "azure_openai",
    "endpoint": "https://west-europe-resource.openai.azure.com/",
    "deployment_name": "gpt-4"
  }
}
```

#### Failover Configuration
```json
{
  "azure_primary": {
    "type": "azure_openai",
    "endpoint": "https://primary-resource.openai.azure.com/",
    "deployment_name": "gpt-4",
    "default": true
  },
  "azure_backup": {
    "type": "azure_openai",
    "endpoint": "https://backup-resource.openai.azure.com/",
    "deployment_name": "gpt-4"
  }
}
```

## 🏠 Local Ollama Provider

### Basis Configuratie
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

### Ollama Modellen

#### Llama Series
```json
{
  "ollama_llama2": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2"
  },
  "ollama_llama2_13b": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2:13b"
  },
  "ollama_codellama": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "codellama"
  }
}
```

#### Mistral Series
```json
{
  "ollama_mistral": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "mistral"
  },
  "ollama_mixtral": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "mixtral"
  }
}
```

### Ollama Best Practices

#### Resource Management
```json
{
  "ollama_lightweight": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2:7b",
    "rate_limit": {
      "requests_per_minute": 500,
      "tokens_per_minute": 500000
    }
  },
  "ollama_heavy": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "mixtral:8x7b",
    "rate_limit": {
      "requests_per_minute": 100,
      "tokens_per_minute": 200000
    }
  }
}
```

#### Multi-Instance Setup
```json
{
  "ollama_instance_1": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2"
  },
  "ollama_instance_2": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11435/v1",
    "model": "mistral"
  }
}
```

## 🔧 Custom Providers

### Generic OpenAI-Compatible
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
      "Custom-Header": "value",
      "Authorization": "Bearer your-token"
    }
  }
}
```

### vLLM Setup
```json
{
  "vllm_server": {
    "type": "openai",
    "api_key": "vllm",
    "base_url": "http://vllm-server:8000/v1",
    "model": "your-model",
    "rate_limit": {
      "requests_per_minute": 2000,
      "tokens_per_minute": 2000000
    }
  }
}
```

### Text Generation Inference (TGI)
```json
{
  "tgi_server": {
    "type": "openai",
    "api_key": "tgi",
    "base_url": "http://tgi-server:8080/v1",
    "model": "your-model",
    "rate_limit": {
      "requests_per_minute": 1500,
      "tokens_per_minute": 1500000
    }
  }
}
```

## 📊 Provider Comparison

### Performance Characteristics

| Provider | Latency | Throughput | Cost | Quality |
|----------|---------|------------|------|---------|
| OpenAI GPT-4 | Medium | Medium | High | Very High |
| OpenAI GPT-3.5 | Low | High | Medium | High |
| Azure OpenAI | Medium | Medium | High | Very High |
| Local Ollama | Variable | Low | Low | Medium-High |
| Custom vLLM | Low | High | Low | High |

### Use Case Recommendations

#### Production Workloads
```json
{
  "production_primary": {
    "type": "openai",
    "model": "gpt-4-turbo-preview",
    "rate_limit": {
      "requests_per_minute": 500,
      "tokens_per_minute": 300000
    }
  },
  "production_backup": {
    "type": "azure_openai",
    "endpoint": "https://backup-resource.openai.azure.com/",
    "deployment_name": "gpt-4"
  }
}
```

#### Development & Testing
```json
{
  "dev_main": {
    "type": "openai",
    "model": "gpt-3.5-turbo",
    "rate_limit": {
      "requests_per_minute": 100,
      "tokens_per_minute": 30000
    }
  },
  "dev_local": {
    "type": "openai",
    "api_key": "ollama",
    "base_url": "http://localhost:11434/v1",
    "model": "llama2:7b"
  }
}
```

#### Cost-Optimized
```json
{
  "cost_optimized": {
    "type": "openai",
    "model": "gpt-3.5-turbo",
    "generation_params": {
      "max_tokens": 300,
      "temperature": 0.1
    }
  }
}
```

#### Quality-Focused
```json
{
  "quality_focused": {
    "type": "openai",
    "model": "gpt-4-turbo-preview",
    "generation_params": {
      "max_tokens": 2000,
      "temperature": 0.1,
      "top_p": 0.95
    }
  }
}
```

## 🔐 Security Configuration

### API Key Management

#### Environment Variables
```bash
# OpenAI
export OPENAI_MAIN_API_KEY="sk-your-openai-key"
export AZURE_OPENAI_API_KEY="your-azure-key"

# Custom providers
export CUSTOM_PROVIDER_API_KEY="your-custom-key"
```

#### Configuration with Fallback
```json
{
  "secure_openai": {
    "type": "openai",
    "api_key": "",
    "base_url": "https://api.openai.com/v1"
  }
}
```

### Network Security

#### SSL Configuration
```json
{
  "secure_provider": {
    "type": "openai",
    "base_url": "https://secure-endpoint.com/v1",
    "verify_ssl": true,
    "ssl_cert_path": "/path/to/cert.pem"
  }
}
```

#### Proxy Configuration
```json
{
  "proxy_provider": {
    "type": "openai",
    "base_url": "https://api.openai.com/v1",
    "proxy": {
      "http": "http://proxy.company.com:8080",
      "https": "https://proxy.company.com:8080"
    }
  }
}
```

## 🚀 Performance Tuning

### Connection Pooling
```json
{
  "high_performance": {
    "type": "openai",
    "rate_limit": {
      "requests_per_minute": 3000,
      "tokens_per_minute": 90000,
      "burst_size": 50
    },
    "connection": {
      "pool_size": 20,
      "max_connections": 100,
      "keep_alive": true
    }
  }
}
```

### Batch Optimization
```json
{
  "batch_optimized": {
    "type": "openai",
    "processing": {
      "batch_size": 50,
      "concurrent_requests": 20,
      "timeout": 60.0
    }
  }
}
```

### Memory Management
```json
{
  "memory_optimized": {
    "type": "openai",
    "processing": {
      "batch_size": 10,
      "save_interval": 50,
      "cache_responses": false
    }
  }
}
```

---

*Deze provider configuratie gids biedt gedetailleerde informatie voor het opzetten van diverse LLM providers met optimale settings voor verschillende use cases.*