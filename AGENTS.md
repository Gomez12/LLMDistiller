# LLM Distiller - Agent Guidelines

## Documentation Requirements
- **ALWAYS read docs/ directory before starting any task** - Complete project documentation and architecture
- **UPDATE docs after completing any task** - Keep documentation current with implementation changes
- **Key docs to review**: `docs/01-overview/` for architecture, `docs/04-api/` for CLI reference, `docs/05-implementation/` for development setup

## Development Commands
- **Install**: `pip install -r requirements.txt && pip install -r requirements-dev.txt`
- **Lint**: `black src/ tests/ && isort src/ tests/ && flake8 src/ tests/`
- **Type check**: `mypy src/`
- **Test single**: `pytest tests/unit/test_file.py::test_function -v`
- **Test all**: `pytest --cov=src --cov-report=html`
- **Run CLI**: `python -m src.main [command]`

## Code Style Guidelines
- **Formatting**: Black (88 char line length), isort for imports
- **Imports**: Group stdlib, third-party, local imports; use absolute imports
- **Types**: Use type hints consistently; prefer `Optional[T]` over `T | None`
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Error handling**: Use specific exceptions, log errors, implement retry logic for external APIs
- **Documentation**: Docstrings for all public functions/classes using Google style
- **Async**: Use async/await for I/O operations, proper exception handling in async code

## Architecture Notes
- Use SQLAlchemy models in `src/database/models/`
- LLM providers inherit from `BaseLLMProvider` in `src/llm/`
- Configuration uses Pydantic models in `src/config/`
- CLI commands in `src/cli/` using Click framework
- Database operations use context managers for session management