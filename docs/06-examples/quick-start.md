# Quick Start

Welkom bij de LLM Distiller! Deze gids helpt je om snel aan de slag te gaan met het distilleren van LLM kennis voor fine-tuning datasets.

## 🚀 Snelstart in 5 Minuten

### 1. Installatie
```bash
# Clone de repository
git clone https://github.com/Gomez12/LLMDistiller.git
cd LLMDistiller

# Setup virtuele omgeving
python -m venv venv
source venv/bin/activate  # Linux/macOS
# of venv\Scripts\activate  # Windows

# Installeer dependencies
pip install -r requirements.txt

# Installeer het package in development mode
pip install -e .
```

### 2. Initialisatie
```bash
# Initialiseer configuratie
llm-distiller init

# Setup je API key
export OPENAI_MAIN_API_KEY="your-openai-api-key"
```

### 3. Importeer Vragen
```bash
# Creëer een sample CSV bestand
cat > questions.csv << EOF
category,question,answer_schema
math,"What is 2+2?","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}"
science,"What is H2O?","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"string\"}}}"
EOF

# Importeer de vragen
llm-distiller import csv questions.csv --default-correct null
```

### 4. Verwerk met LLM
```bash
# Verwerk de vragen met OpenAI
llm-distiller process --limit 2
```

### 5. Exporteer Dataset
```bash
# Exporteer voor fine-tuning
llm-distiller export --correct-only --output dataset.jsonl
```

## 📋 Wat je nu hebt

- **Database**: SQLite database met vragen en antwoorden
- **Responses**: LLM antwoorden met metadata
- **Dataset**: JSONL bestand klaar voor fine-tuning

## 🎯 Volgende Stappen

### 1. Valideer Antwoorden
```bash
# Bekijk antwoorden
llm-distiller stats validation

# Markeer correct/incorrect
llm-distiller validate set 1 --correct
llm-distiller validate set 2 --incorrect
```

### 2. Importeer Grotere Dataset
```bash
# Import uit JSON bestand
llm-distiller import json large_dataset.json

# Import uit database
llm-distiller import db "postgresql://user:pass@host/db" --query "SELECT * FROM questions"
```

### 3. Gebruik Meerdere Providers
```bash
# Voeg lokale Ollama toe
llm-distiller config show --provider local_ollama

# Verwerk met specifieke provider
llm-distiller process --provider local_ollama --limit 10
```

## 📊 Voorbeeld Workflows

### Math Problems Dataset
```bash
# 1. Importeer wiskunde vragen
llm-distiller import csv math_problems.csv --category math

# 2. Verwerk met GPT-4
llm-distiller process --category math --model gpt-4

# 3. Valideer antwoorden
llm-distiller validate batch math_validations.csv

# 4. Exporteer training data
llm-distiller export --category math --correct-only --output math_dataset.jsonl
```

### Code Generation Dataset
```bash
# 1. Importeer code vragen
llm-distiller import json code_questions.json

# 2. Verwerk met reasoning model
llm-distiller process --model gpt-4 --temperature 0.1

# 3. Exporteer met reasoning
llm-distiller export --include-reasoning --output code_dataset.jsonl
```

## 🔧 Configuratie Voorbeelden

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
    "console": true
  }
}
```

### Production Setup
```json
{
  "database": {
    "url": "postgresql://user:pass@prod-db:5432/llm_distiller",
    "pool_size": 20
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
    "batch_size": 50,
    "concurrent_requests": 10
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llm_distiller/app.log"
  }
}
```

## 📁 Data Formaten

### CSV Format
```csv
json_id,category,question,golden_answer,answer_schema
1,math,"What is 2+2?","4","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}"
2,science,"What is H2O?","Water","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"string\"}}}"
```

### JSON Format
```json
{
  "questions": [
    {
      "json_id": "1",
      "category": "math",
      "question": "What is 2+2?",
      "golden_answer": "4",
      "answer_schema": {
        "type": "object",
        "properties": {
          "answer": {"type": "number"}
        }
      }
    }
  ]
}
```

### Export JSONL Format
```json
{"question": "What is 2+2?", "answer": "4", "category": "math", "model": "gpt-4"}
{"question": "What is H2O?", "answer": "Water", "category": "science", "model": "gpt-4"}
```

## 🛠️ Handige Commands

### Database Operations
```bash
# Database status
llm-distiller stats db

# Toon vragen
llm-distiller search questions "math"

# Toon antwoorden
llm-distiller search responses "derivative"
```

### Processing Control
```bash
# Verwerk specifieke vragen
llm-distiller process --question-ids 1,2,3

# Verwerk per categorie
llm-distiller process --category science

# Dry run
llm-distiller process --limit 5 --dry-run
```

### Export Options
```bash
# Exporteer alles
llm-distiller export --output all_data.jsonl

# Exporteer alleen correcte
llm-distiller export --correct-only --output training_data.jsonl

# Exporteer per categorie
llm-distiller export --category math --output math_data.jsonl

# Exporteer met metadata
llm-distiller export --include-metadata --output full_data.jsonl
```

## 🔍 Probleemoplossing

### Veelvoorkomende Issues

#### API Key Problemen
```bash
# Check configuratie
llm-distiller config test

# Check environment variable
echo $OPENAI_MAIN_API_KEY

# Test verbinding
llm-distiller config test --provider openai_main
```

#### Database Problemen
```bash
# Check database status
llm-distiller stats db

# Reset database (development)
rm llm_distiller.db
llm-distiller init
```

#### Rate Limiting
```bash
# Check rate limits
llm-distiller stats model

# Verlaag batch size
llm-distiller process --batch-size 5
```

### Debug Mode
```bash
# Enable verbose logging
llm-distiller --verbose process --limit 1

# Check configuratie
llm-distiller config show --mask-secrets false
```

## 📚 Verdere Lezen

- **[Project Overview](../01-overview/project-overview.md)** - Gedetailleerde project beschrijving
- **[Architecture](../01-overview/architecture.md)** - Systeemarchitectuur
- **[CLI Reference](../04-api/cli-reference.md)** - Compleet commando overzicht
- **[Configuration](../03-configuration/config-reference.md)** - Configuratie opties
- **[Examples](../03-configuration/examples/)** - Meer configuratie voorbeelden

## 🤝 Community

- **GitHub Issues**: Rapporteer bugs en request features
- **Discussions**: Stel vragen en deel ideeën
- **Contributing**: Zie [Contributing Guide](../05-implementation/contributing.md)

---

*Succes met de LLM Distiller! Voor vragen of problemen, check de documentatie of open een issue op GitHub.*