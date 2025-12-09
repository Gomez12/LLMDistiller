# Development Setup

Dit document beschrijft hoe je een development omgeving opzet voor de LLM Distiller, inclusief dependencies, configuratie en development workflows.

## 📋 Vereisten

### System Vereisten
- **Python**: 3.9 of hoger
- **Operating System**: Linux, macOS, of Windows
- **Memory**: Minimaal 4GB RAM (8GB aanbevolen)
- **Storage**: Minimaal 10GB vrije schijfruimte
- **Network**: Internet connectie voor LLM API calls

### Software Vereisten
- **Git**: Voor version control
- **Python Package Manager**: pip of poetry
- **Database**: SQLite (standaard) of PostgreSQL/MySQL (optioneel)
- **LLM Provider**: OpenAI API key of lokale LLM setup

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/LLMDistiller.git
cd LLMDistiller
```

### 2. Create Virtual Environment
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# of
venv\Scripts\activate     # Windows

# Using conda
conda create -n llm-distiller python=3.9
conda activate llm-distiller
```

### 3. Install Dependencies
```bash
# Using pip
pip install -r requirements.txt

# Using poetry (optioneel)
poetry install
poetry shell
```

### 4. Initialize Configuration
```bash
# Create default configuration
llm-distiller init

# Of met custom pad
llm-distiller init --config-path ./my-config
```

### 5. Setup Environment Variables
```bash
# OpenAI API key
export OPENAI_MAIN_API_KEY="your-openai-api-key"

# Azure OpenAI (optioneel)
export AZURE_OPENAI_API_KEY="your-azure-api-key"

# Custom providers
export CUSTOM_PROVIDER_API_KEY="your-custom-key"
```

### 6. Initialize Database
```bash
# Run database migrations
alembic upgrade head

# Of via CLI
llm-distiller maintenance init-db
```

### 7. Test Installation
```bash
# Test configuration
llm-distiller config test

# Test met sample data
llm-distiller import csv --file examples/sample_questions.csv --dry-run
```

## 📦 Dependencies

### Core Dependencies
```txt
# requirements.txt
# Core Framework
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
click>=8.0.0

# LLM Integration
openai>=1.0.0
httpx>=0.24.0
aiohttp>=3.8.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
jsonschema>=4.0.0
lxml>=4.9.0
chardet>=5.0.0

# Database Drivers
sqlite3  # Built-in
psycopg2-binary>=2.9.0  # PostgreSQL
PyMySQL>=1.0.0  # MySQL
pymssql>=2.2.0  # SQL Server

# Utilities
python-dotenv>=1.0.0
pyyaml>=6.0.0
tqdm>=4.64.0
rich>=13.0.0

# Async Support
asyncio-throttle>=1.0.0
aiofiles>=23.0.0
```

### Development Dependencies
```txt
# requirements-dev.txt
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0
pre-commit>=3.0.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.0.0
mkdocstrings>=0.22.0

# Development Tools
ipython>=8.0.0
jupyter>=1.0.0
python-lsp-server>=1.7.0
```

### Optional Dependencies
```txt
# requirements-optional.txt
# Local LLM Support
ollama-python>=0.1.0

# Advanced Processing
scikit-learn>=1.3.0
transformers>=4.30.0
torch>=2.0.0

# Monitoring
prometheus-client>=0.16.0
structlog>=23.0.0

# Web Interface (future)
gradio>=3.35.0
fastapi>=0.100.0
uvicorn>=0.22.0
```

## 🏗️ Project Structuur

### Development Layout
```
LLMDistiller/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── cli/                    # CLI commands
│   ├── database/               # Database models en migrations
│   ├── llm/                   # LLM providers
│   ├── data_import/            # Data importers
│   ├── validation/            # Schema validation
│   ├── rate_limiting/         # Rate limiting
│   ├── export/                # Data export
│   └── config/                # Configuration management
├── tests/                     # Test files
├── docs/                      # Documentation
├── config/                    # Configuration files
├── examples/                  # Example data en scripts
├── alembic/                   # Database migrations
├── logs/                      # Log files
├── venv/                      # Virtual environment
├── requirements.txt           # Dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project metadata
├── .gitignore               # Git ignore file
├── .pre-commit-config.yaml  # Pre-commit hooks
└── README.md                # Project description
```

### Development Tools Setup

#### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## ⚙️ Development Configuration

### Development Configuratie
```json
{
  "database": {
    "url": "sqlite:///dev_llm_distiller.db",
    "echo": true
  },
  "llm_providers": {
    "dev_openai": {
      "type": "openai",
      "api_key": "",
      "model": "gpt-3.5-turbo",
      "rate_limit": {
        "requests_per_minute": 10,
        "tokens_per_minute": 5000
      },
      "default": true
    },
    "local_ollama": {
      "type": "openai",
      "api_key": "ollama",
      "base_url": "http://localhost:11434/v1",
      "model": "llama2:7b"
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

### Environment Variables
```bash
# .env.development
# Database
DATABASE_URL=sqlite:///dev_llm_distiller.db

# LLM Providers
OPENAI_MAIN_API_KEY=your-dev-api-key
AZURE_OPENAI_API_KEY=your-azure-dev-key

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG
TESTING=false

# Optional: Local LLM
OLLAMA_BASE_URL=http://localhost:11434
```

### Testing Environment
```bash
# .env.testing
DATABASE_URL=sqlite:///:memory:
OPENAI_MAIN_API_KEY=test-key
DEBUG=true
TESTING=true
LOG_LEVEL=WARNING
```

## 🧪 Testing Setup

### Test Structure
```
tests/
├── conftest.py              # Pytest configuration
├── unit/                    # Unit tests
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_importers.py
├── integration/             # Integration tests
│   ├── test_database.py
│   ├── test_llm_client.py
│   └── test_cli.py
├── e2e/                     # End-to-end tests
│   ├── test_workflows.py
│   └── test_scenarios.py
├── fixtures/                # Test data
│   ├── sample_questions.csv
│   ├── test_schemas.json
│   └── mock_responses.json
└── helpers/                 # Test utilities
    ├── mock_providers.py
    ├── test_utils.py
    └── database_helpers.py
```

### Pytest Configuration
```python
# conftest.py
import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.config.settings import Settings

@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings"""
    return Settings(
        database={
            "url": "sqlite:///:memory:",
            "echo": False
        },
        llm_providers={
            "test_provider": {
                "type": "openai",
                "api_key": "test-key",
                "base_url": "http://localhost:9999/v1",
                "model": "test-model"
            }
        },
        default_provider="test_provider",
        processing={
            "batch_size": 1,
            "concurrent_requests": 1
        },
        logging={
            "level": "WARNING"
        }
    )

@pytest.fixture
def test_db(test_settings):
    """Test database session"""
    engine = create_engine(test_settings.database.url)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def temp_config_file():
    """Temporary configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "database": {"url": "sqlite:///:memory:"},
            "llm_providers": {
                "test": {
                    "type": "openai",
                    "api_key": "test-key"
                }
            }
        }
        import json
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)

@pytest.fixture
def sample_questions():
    """Sample question data for testing"""
    return [
        {
            "json_id": "1",
            "category": "math",
            "question": "What is 2+2?",
            "golden_answer": "4",
            "answer_schema": '{"type": "object", "properties": {"answer": {"type": "number"}}}'
        },
        {
            "json_id": "2",
            "category": "science",
            "question": "What is H2O?",
            "golden_answer": "Water",
            "answer_schema": '{"type": "object", "properties": {"answer": {"type": "string"}}}'
        }
    ]
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"

# Run integration tests
pytest tests/integration/

# Run with specific markers
pytest -m "unit"
pytest -m "integration"
pytest -m "e2e"
```

## 🔧 Development Workflows

### Code Quality Workflow
```bash
# 1. Install pre-commit hooks
pre-commit install

# 2. Make changes
# ... edit files ...

# 3. Run pre-commit hooks manually
pre-commit run --all-files

# 4. Run tests
pytest

# 5. Check code coverage
pytest --cov=src --cov-report=term-missing

# 6. Type checking
mypy src/

# 7. Security check
bandit -r src/
```

### Feature Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/new-importer

# 2. Develop feature
# ... write code ...

# 3. Add tests
# ... write tests ...

# 4. Run test suite
pytest

# 5. Check code quality
pre-commit run --all-files

# 6. Update documentation
# ... update docs ...

# 7. Commit changes
git add .
git commit -m "feat: add new data importer"

# 8. Push and create PR
git push origin feature/new-importer
```

### Debugging Setup

#### VS Code Debug Configuration
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug CLI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "args": ["import", "csv", "--file", "examples/sample.csv", "--dry-run"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        },
        {
            "name": "Debug Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/pytest",
            "args": ["tests/unit/test_models.py::test_question_creation", "-v", "-s"],
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

#### Logging Configuration
```python
# src/utils/debug_logging.py
import logging
import sys
from pathlib import Path

def setup_debug_logging():
    """Setup enhanced logging for debugging"""
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/debug.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Enable specific debug loggers
    debug_loggers = [
        'src.database',
        'src.llm',
        'src.validation',
        'src.rate_limiting'
    ]
    
    for logger_name in debug_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.FileHandler(f'logs/{logger_name.replace(".", "_")}.log'))
```

## 📊 Performance Monitoring

### Development Monitoring
```python
# src/utils/performance.py
import time
import functools
from typing import Callable, Any

def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"[PERF] {func.__name__} took {execution_time:.4f} seconds")
        
        return result
    
    return wrapper

def memory_usage():
    """Get current memory usage"""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB

def profile_function(func: Callable) -> Callable:
    """Decorator to profile function performance"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import cProfile
        import pstats
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 functions
        
        return result
    
    return wrapper
```

### Development Metrics
```bash
# Install monitoring dependencies
pip install memory-profiler psutil

# Profile memory usage
python -m memory_profiler src/main.py import csv --file sample.csv

# Profile execution time
python -m cProfile -o profile.stats src/main.py import csv --file sample.csv
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

## 🐛 Common Issues

### Installation Issues

#### Python Version Conflicts
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m venv venv
source venv/bin/activate
```

#### Dependency Conflicts
```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Use pip-tools for dependency resolution
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

### Database Issues

#### SQLite Lock Errors
```bash
# Check for locked database
lsof | grep llm_distiller.db

# Remove lock file (if safe)
rm -f llm_distiller.db-journal
```

#### Migration Issues
```bash
# Check current migration
alembic current

# Reset migrations (development only)
alembic downgrade base
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "fix migration"
```

### LLM Provider Issues

#### API Key Problems
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check environment variables
env | grep API_KEY
```

#### Rate Limiting
```bash
# Check rate limits
llm-distiller stats model --provider openai_main

# Adjust rate limits in config
# Edit config/config.json
```

## 🚀 Deployment Preparation

### Build Process
```bash
# Install build dependencies
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Install locally for testing
pip install dist/llm_distiller-1.0.0-py3-none-any.whl
```

### Docker Development
```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Setup environment
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Development command
CMD ["python", "-m", "src.main", "--help"]
```

### Docker Compose for Development
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  llm-distiller:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: llm_distiller
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

*Deze development setup gids biedt een complete basis voor het opzetten van een productieve development omgeving voor de LLM Distiller.*