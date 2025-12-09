# LLM Distiller Documentation

Welcome to the comprehensive documentation for the LLM Distiller project. This system is designed to create high-quality datasets for fine-tuning smaller language models by distilling knowledge from larger LLMs.

## 📚 Documentation Structure

### [01. Project Overview](./01-overview/)
- **[Project Overview](./01-overview/project-overview.md)** - Goals, scope, and objectives
- **[Architecture](./01-overview/architecture.md)** - System architecture and design
- **[Design Decisions](./01-overview/design-decisions.md)** - Key architectural choices

### [02. Database](./02-database/)
- **[Schema](./02-database/schema.md)** - Complete database schema documentation
- **[Models](./02-database/models.md)** - SQLAlchemy models and relationships
- **[Migrations](./02-database/migrations.md)** - Database migration strategy

### [03. Configuration](./03-configuration/)
- **[Configuration Reference](./03-configuration/config-reference.md)** - Complete configuration guide
- **[LLM Providers](./03-configuration/providers.md)** - Provider-specific configuration
- **[Examples](./03-configuration/examples/)** - Configuration examples and templates

### [04. API & CLI](./04-api/)
- **[CLI Reference](./04-api/cli-reference.md)** - Complete command-line interface reference
- **[Data Importers](./04-api/importers.md)** - Import module documentation
- **[LLM Client](./04-api/llm-client.md)** - LLM integration and client usage
- **[Validation](./04-api/validation.md)** - JSON schema validation system

### [05. Implementation](./05-implementation/)
- **[Development Setup](./05-implementation/setup.md)** - Setting up the development environment
- **[Contributing](./05-implementation/contributing.md)** - Contribution guidelines
- **[Testing](./05-implementation/testing.md)** - Testing strategy and frameworks

### [06. Examples](./06-examples/)
- **[Quick Start](./06-examples/quick-start.md)** - Get started in minutes
- **[Workflows](./06-examples/workflows/)** - Common usage workflows
- **[Use Cases](./06-examples/use-cases.md)** - Real-world implementation examples

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize configuration**:
   ```bash
   llm-distiller init --config-path ./config
   ```

3. **Import your first dataset**:
   ```bash
   llm-distiller import csv --file questions.csv --default-correct null
   ```

4. **Process with LLM**:
   ```bash
   llm-distiller process --provider openai_main --limit 10
   ```

5. **Export training data**:
   ```bash
   llm-distiller export --format jsonl --output dataset.jsonl --correct-only
   ```

## 🎯 Core Concepts

### Questions & Responses
The system stores questions and their corresponding LLM responses, with support for:
- **Golden answers** (reference responses)
- **JSON schema validation** for structured outputs
- **Manual validation** through the `is_correct` field
- **Invalid response tracking** for debugging

### Multi-Provider Support
Configure multiple LLM providers:
- OpenAI (cloud and local)
- Azure OpenAI
- Custom OpenAI-compatible endpoints
- Provider-specific rate limiting

### Data Import Flexibility
Import from various sources:
- CSV files with custom mapping
- JSON/XML files
- External databases (PostgreSQL, SQL Server, etc.)
- Batch processing with progress tracking

## 🔧 Key Features

- **Flexible Database**: SQLite with SQLAlchemy for future migration
- **Rate Limiting**: Configurable limits with API-aware throttling
- **Schema Validation**: JSON schema validation with error tracking
- **CLI-First**: Complete command-line interface
- **Future-Ready**: Prepared for Gradio web interface
- **Export Options**: Multiple formats for fine-tuning datasets

## 📖 Getting Help

- Check the [Examples](./06-examples/) section for common workflows
- Review the [CLI Reference](./04-api/cli-reference.md) for command details
- See [Configuration](./03-configuration/) for setup options
- Visit [Implementation Guide](./05-implementation/) for development help

---

*This documentation serves as the complete reference for the LLM Distiller project. It covers everything from initial setup to advanced usage patterns.*