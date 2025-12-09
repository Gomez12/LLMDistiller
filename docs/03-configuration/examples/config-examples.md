# Configuration Examples

Dit document bevat praktische configuratie voorbeelden voor verschillende scenario's en omgevingen.

## 📋 Overzicht

Voorbeelden voor:
- **Development**: Lokale ontwikkeling setup
- **Production**: Productie omgeving
- **Multi-provider**: Failover en load balancing
- **High-throughput**: Grootschalige verwerking
- **Cost-optimized**: Kostenbesparende configuraties

## 🚀 Quick Start

Gebruik het meegeleverde `config.example.json` bestand als startpunt:

```bash
# Kopieer de voorbeeld configuratie
cp config.example.json config.json

# Bewerk met je instellingen
nano config.json
```

Het voorbeeld bevat drie vooraf geconfigureerde providers:
1. **openai_main**: OpenAI API (standaard)
2. **local_ollama**: Lokale Ollama server
3. **azure_openai**: Azure OpenAI service

Voeg je API keys toe via environment variables:
```bash
export OPENAI_API_KEY="jouw-openai-key"
export AZURE_OPENAI_API_KEY="jouw-azure-key"
```

## 🛠️ Development Setup

### Basic Development
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
      "model": "llama2:7b",
      "default": true
    }
  },
  "processing": {
    "batch_size": 5,
    "concurrent_requests": 2,
    "timeout": 30.0
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "console_level": "DEBUG",
    "file": "logs/dev.log"
  }
}
```

### Development with OpenAI
```json
{
  "database": {
    "url": "sqlite:///dev_llm_distiller.db",
    "echo": true
  },
  "llm_providers": {
    "openai_dev": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 10,
        "tokens_per_minute": 10000
      },
      "default": true
    },
    "local_backup": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://localhost:11434/v1",
      "model": "llama2:7b"
    }
  },
  "processing": {
    "batch_size": 3,
    "max_retries": 2,
    "timeout": 20.0
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "file": "logs/dev.log"
  }
}
```

### Testing Configuration
```json
{
  "database": {
    "url": "sqlite:///:memory:",
    "echo": false
  },
  "llm_providers": {
    "mock_provider": {
      "type": "openai",
      "api_key": "mock",
      "base_url": "http://localhost:9999/v1",
      "model": "mock-model",
      "default": true
    }
  },
  "processing": {
    "batch_size": 1,
    "concurrent_requests": 1,
    "timeout": 5.0,
    "max_retries": 1
  },
  "logging": {
    "level": "WARNING",
    "console": false
  }
}
```

## 🏭 Production Setup

### Basic Production
```json
{
  "database": {
    "url": "postgresql://prod_user:secure_pass@db.example.com:5432/llm_distiller",
    "pool_size": 20,
    "max_overflow": 30,
    "echo": false
  },
  "llm_providers": {
    "openai_prod": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "rate_limit": {
        "requests_per_minute": 500,
        "tokens_per_minute": 300000
      },
      "default": true
    }
  },
  "processing": {
    "batch_size": 20,
    "concurrent_requests": 10,
    "timeout": 60.0,
    "max_retries": 3
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

### Production with Failover
```json
{
  "database": {
    "url": "postgresql://prod_user:secure_pass@db-primary.example.com:5432/llm_distiller",
    "pool_size": 20,
    "max_overflow": 30
  },
  "llm_providers": {
    "openai_primary": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "rate_limit": {
        "requests_per_minute": 500,
        "tokens_per_minute": 300000
      },
      "default": true
    },
    "azure_backup": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://backup-resource.openai.azure.com/",
      "deployment_name": "gpt-4",
      "rate_limit": {
        "requests_per_minute": 300,
        "tokens_per_minute": 120000
      }
    },
    "openai_secondary": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 90000
      }
    }
  },
  "processing": {
    "batch_size": 25,
    "concurrent_requests": 15,
    "timeout": 60.0,
    "max_retries": 3
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

### Enterprise Production
```json
{
  "database": {
    "url": "postgresql://prod_user:secure_pass@db-cluster.example.com:5432/llm_distiller",
    "pool_size": 50,
    "max_overflow": 100,
    "connect_timeout": 30,
    "recycle": 3600
  },
  "llm_providers": {
    "azure_ptu_primary": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://ptu-primary.openai.azure.com/",
      "deployment_name": "gpt-4",
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 600000
      },
      "default": true
    },
    "azure_ptu_secondary": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://ptu-secondary.openai.azure.com/",
      "deployment_name": "gpt-4",
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 600000
      }
    },
    "openai_enterprise": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 300000
      }
    }
  },
  "processing": {
    "batch_size": 100,
    "concurrent_requests": 50,
    "timeout": 120.0,
    "max_retries": 5,
    "save_interval": 500
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llm_distiller/app.log",
    "console": false,
    "max_size": "500MB",
    "backup_count": 20,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d"
  },
  "monitoring": {
    "metrics_enabled": true,
    "health_check_interval": 30,
    "alert_thresholds": {
      "error_rate": 0.05,
      "response_time": 30.0,
      "queue_size": 1000
    }
  }
}
```

## 🔄 Multi-Provider Setup

### Load Balancing
```json
{
  "database": {
    "url": "sqlite:///llm_distiller.db"
  },
  "llm_providers": {
    "openai_1": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 90000
      }
    },
    "openai_2": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 90000
      }
    },
    "azure_1": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://azure-1.openai.azure.com/",
      "deployment_name": "gpt-35-turbo",
      "rate_limit": {
        "requests_per_minute": 300,
        "tokens_per_minute": 120000
      }
    }
  },
  "processing": {
    "batch_size": 30,
    "concurrent_requests": 20,
    "load_balancing": {
      "strategy": "round_robin",
      "health_check": true,
      "failover_timeout": 30
    }
  }
}
```

### Quality Tier Setup
```json
{
  "database": {
    "url": "sqlite:///llm_distiller.db"
  },
  "llm_providers": {
    "premium_quality": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "rate_limit": {
        "requests_per_minute": 100,
        "tokens_per_minute": 300000
      }
    },
    "standard_quality": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 90000
      },
      "default": true
    },
    "budget_quality": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "generation_params": {
        "max_tokens": 300,
        "temperature": 0.3
      },
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 60000
      }
    }
  },
  "processing": {
    "batch_size": 20,
    "concurrent_requests": 10
  }
}
```

### Hybrid Cloud Setup
```json
{
  "database": {
    "url": "postgresql://user:pass@cloud-db.example.com:5432/llm_distiller"
  },
  "llm_providers": {
    "cloud_primary": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "rate_limit": {
        "requests_per_minute": 500,
        "tokens_per_minute": 300000
      },
      "default": true
    },
    "local_fallback": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://local-server:11434/v1",
      "model": "mixtral:8x7b",
      "rate_limit": {
        "requests_per_minute": 500,
        "tokens_per_minute": 1000000
      }
    },
    "edge_compute": {
      "type": "openai",
      "api_key": "edge-key",
      "base_url": "https://edge-server.example.com/v1",
      "model": "local-model",
      "rate_limit": {
        "requests_per_minute": 200,
        "tokens_per_minute": 500000
      }
    }
  },
  "processing": {
    "batch_size": 25,
    "concurrent_requests": 15,
    "failover_strategy": "geographic"
  }
}
```

## 🚀 High-Throughput Setup

### Maximum Performance
```json
{
  "database": {
    "url": "postgresql://user:pass@high-perf-db.example.com:5432/llm_distiller",
    "pool_size": 100,
    "max_overflow": 200,
    "connect_timeout": 10
  },
  "llm_providers": {
    "openai_high_1": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 3000,
        "tokens_per_minute": 90000
      }
    },
    "openai_high_2": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 3000,
        "tokens_per_minute": 90000
      }
    },
    "azure_high": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://high-perf.openai.azure.com/",
      "deployment_name": "gpt-35-turbo",
      "rate_limit": {
        "requests_per_minute": 3000,
        "tokens_per_minute": 300000
      }
    }
  },
  "processing": {
    "batch_size": 200,
    "concurrent_requests": 100,
    "timeout": 30.0,
    "max_retries": 2,
    "save_interval": 1000,
    "memory_optimization": true,
    "connection_pooling": {
      "max_connections": 500,
      "keep_alive": true,
      "timeout": 60
    }
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/llm_distiller/high-throughput.log",
    "async_logging": true
  }
}
```

### Distributed Processing
```json
{
  "database": {
    "url": "postgresql://user:pass@distributed-db.example.com:5432/llm_distiller",
    "pool_size": 50,
    "max_overflow": 100
  },
  "llm_providers": {
    "cluster_node_1": {
      "type": "openai",
      "api_key": "",
      "base_url": "http://node-1.example.com:8000/v1",
      "model": "distributed-model",
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 1000000
      }
    },
    "cluster_node_2": {
      "type": "openai",
      "api_key": "",
      "base_url": "http://node-2.example.com:8000/v1",
      "model": "distributed-model",
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 1000000
      }
    },
    "cluster_node_3": {
      "type": "openai",
      "api_key": "",
      "base_url": "http://node-3.example.com:8000/v1",
      "model": "distributed-model",
      "rate_limit": {
        "requests_per_minute": 2000,
        "tokens_per_minute": 1000000
      }
    }
  },
  "processing": {
    "batch_size": 150,
    "concurrent_requests": 75,
    "distributed": {
      "enabled": true,
      "strategy": "hash_based",
      "node_health_check": true,
      "auto_failover": true
    }
  }
}
```

## 💰 Cost-Optimized Setup

### Budget Configuration
```json
{
  "database": {
    "url": "sqlite:///budget_llm_distiller.db"
  },
  "llm_providers": {
    "budget_main": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "generation_params": {
        "max_tokens": 300,
        "temperature": 0.1,
        "top_p": 0.9
      },
      "rate_limit": {
        "requests_per_minute": 500,
        "tokens_per_minute": 30000
      },
      "default": true
    },
    "local_free": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://localhost:11434/v1",
      "model": "llama2:7b",
      "rate_limit": {
        "requests_per_minute": 1000,
        "tokens_per_minute": 1000000
      }
    }
  },
  "processing": {
    "batch_size": 50,
    "concurrent_requests": 5,
    "cost_tracking": {
      "enabled": true,
      "daily_budget": 10.0,
      "alert_threshold": 0.8
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/budget.log"
  }
}
```

### Tiered Cost Strategy
```json
{
  "database": {
    "url": "sqlite:///tiered_llm_distiller.db"
  },
  "llm_providers": {
    "free_tier": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "generation_params": {
        "max_tokens": 150,
        "temperature": 0.0
      },
      "rate_limit": {
        "requests_per_minute": 3,
        "tokens_per_minute": 40000
      }
    },
    "budget_tier": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "generation_params": {
        "max_tokens": 500,
        "temperature": 0.2
      },
      "rate_limit": {
        "requests_per_minute": 100,
        "tokens_per_minute": 50000
      }
    },
    "premium_tier": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-4-turbo-preview",
      "generation_params": {
        "max_tokens": 1000,
        "temperature": 0.1
      },
      "rate_limit": {
        "requests_per_minute": 50,
        "tokens_per_minute": 100000
      }
    }
  },
  "processing": {
    "batch_size": 20,
    "concurrent_requests": 3,
    "cost_optimization": {
      "strategy": "tiered",
      "auto_downgrade": true,
      "budget_alerts": true
    }
  }
}
```

## 🔒 Security-Focused Setup

### Secure Production
```json
{
  "database": {
    "url": "postgresql://user:secure_pass@secure-db.example.com:5432/llm_distiller",
    "ssl_mode": "require",
    "ssl_cert": "/path/to/client-cert.pem",
    "ssl_key": "/path/to/client-key.pem"
  },
  "llm_providers": {
    "secure_openai": {
      "type": "openai",
      "api_key": "",
      "base_url": "https://api.openai.com/v1",
      "model": "gpt-4-turbo-preview",
      "security": {
        "verify_ssl": true,
        "ssl_cert_path": "/path/to/ca-cert.pem",
        "headers": {
          "User-Agent": "LLMDistiller/1.0"
        }
      },
      "rate_limit": {
        "requests_per_minute": 100,
        "tokens_per_minute": 300000
      },
      "default": true
    }
  },
  "processing": {
    "batch_size": 10,
    "concurrent_requests": 5,
    "security": {
      "encrypt_responses": true,
      "mask_api_keys": true,
      "audit_logging": true
    }
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llm_distiller/secure.log",
    "audit_file": "/var/log/llm_distiller/audit.log",
    "mask_sensitive_data": true
  }
}
```

### Compliance Setup
```json
{
  "database": {
    "url": "postgresql://user:pass@compliance-db.example.com:5432/llm_distiller",
    "encryption": {
      "at_rest": true,
      "in_transit": true,
      "key_rotation": true
    }
  },
  "llm_providers": {
    "compliance_provider": {
      "type": "azure_openai",
      "api_key": "",
      "endpoint": "https://compliance.openai.azure.com/",
      "deployment_name": "gpt-4",
      "compliance": {
        "data_residency": "EU",
        "gdpr_compliant": true,
        "audit_trail": true,
        "data_retention": 30
      }
    }
  },
  "processing": {
    "batch_size": 5,
    "concurrent_requests": 2,
    "compliance": {
      "pii_detection": true,
      "data_anonymization": true,
      "consent_management": true
    }
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llm_distiller/compliance.log",
    "retention_days": 2555,
    "gdpr_compliant": true
  }
}
```

## 🧪 Testing & Validation

### Integration Testing
```json
{
  "database": {
    "url": "sqlite:///test_llm_distiller.db",
    "echo": true
  },
  "llm_providers": {
    "test_openai": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 5,
        "tokens_per_minute": 5000
      },
      "testing": {
        "mock_responses": false,
        "validate_schemas": true,
        "capture_requests": true
      }
    }
  },
  "processing": {
    "batch_size": 2,
    "concurrent_requests": 1,
    "timeout": 10.0,
    "testing": {
      "dry_run": false,
      "validate_before_process": true,
      "capture_metrics": true
    }
  },
  "logging": {
    "level": "DEBUG",
    "console": true,
    "file": "logs/test.log",
    "testing": {
      "capture_all_requests": true,
      "performance_profiling": true
    }
  }
}
```

---

*Deze configuratie voorbeelden dekken veelvoorkomende scenario's en kunnen als startpunt dienen voor je eigen setup.*