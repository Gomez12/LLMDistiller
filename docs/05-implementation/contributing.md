# Contributing Guidelines

Dit document beschrijft hoe je kunt bijdragen aan de LLM Distiller project, inclusief development workflow, code standards en pull request process.

## 📋 Overzicht

Bijdragen zijn welkom in de vorm van:
- **Bug fixes**: Reparaties voor bekende problemen
- **Features**: Nieuwe functionaliteit
- **Documentation**: Verbeteringen aan documentatie
- **Tests**: Test coverage en test verbeteringen
- **Performance**: Optimalisaties en verbeteringen

## 🚀 Quick Start voor Contributors

### 1. Fork en Clone
```bash
# Fork de repository op GitHub
# Clone je fork
git clone https://github.com/YOUR_USERNAME/LLMDistiller.git
cd LLMDistiller

# Voeg upstream remote toe
git remote add upstream https://github.com/ORIGINAL_OWNER/LLMDistiller.git
```

### 2. Setup Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# of venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Create Feature Branch
```bash
# Sync met upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 4. Maak Je Changes
```bash
# Schrijf code
# Voeg tests toe
# Update documentatie

# Run tests en quality checks
pytest
pre-commit run --all-files
```

### 5. Submit Pull Request
```bash
# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push naar je fork
git push origin feature/your-feature-name

# Create pull request op GitHub
```

## 📝 Development Workflow

### Branch Naming Conventions

#### Feature Branches
```bash
feature/new-importer-format
feature/json-schema-validation
feature/gradio-interface
```

#### Bug Fix Branches
```bash
fix/database-connection-leak
fix/rate-limiting-bug
fix/csv-import-parsing
```

#### Documentation Branches
```bash
docs/api-reference-update
docs/installation-guide
docs/examples-addition
```

#### Hotfix Branches
```bash
hotfix/critical-security-fix
hotfix/production-bug-fix
```

### Commit Message Conventions

Gebruik [Conventional Commits](https://www.conventionalcommits.org/) format:

#### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types
- `feat`: Nieuwe feature
- `fix`: Bug fix
- `docs`: Documentatie wijzigingen
- `style`: Code style wijzigingen (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test toevoegingen of wijzigingen
- `chore`: Maintenance wijzigingen
- `perf`: Performance verbeteringen
- `ci`: CI/CD wijzigingen

#### Voorbeelden
```bash
feat(importer): add XML data importer support

Add comprehensive XML import functionality with XPath support,
namespace handling, and error reporting.

Closes #123
```

```bash
fix(database): resolve connection pool exhaustion

Implement proper connection cleanup and add connection health checks
to prevent database connection leaks under high load.

Fixes #456
```

```bash
docs(cli): update import command documentation

Add examples for CSV mapping configuration and clarify
field naming conventions.
```

## 🧪 Testing Standards

### Test Coverage Requirements
- **Unit tests**: Minimaal 80% coverage
- **Integration tests**: Kritieke workflows moeten getest worden
- **E2E tests**: Belangrijke user scenarios

### Test Structure
```
tests/
├── unit/                    # Unit tests
│   ├── test_models.py       # Model tests
│   ├── test_validators.py   # Validation tests
│   ├── test_importers.py    # Importer tests
│   └── test_llm_client.py  # LLM client tests
├── integration/             # Integration tests
│   ├── test_database.py     # Database integration
│   ├── test_api.py          # API integration
│   └── test_workflows.py    # Workflow integration
├── e2e/                     # End-to-end tests
│   ├── test_scenarios.py    # User scenarios
│   └── test_performance.py  # Performance tests
├── fixtures/                # Test data
│   ├── sample_data.csv
│   ├── test_schemas.json
│   └── mock_responses.py
└── helpers/                 # Test utilities
    ├── mock_providers.py
    ├── database_utils.py
    └── test_helpers.py
```

### Test Writing Guidelines

#### Unit Tests
```python
# tests/unit/test_models.py
import pytest
from src.database.models import Question

class TestQuestion:
    """Test Question model functionality"""
    
    def test_question_creation(self):
        """Test basic question creation"""
        question = Question(
            category="math",
            question_text="What is 2+2?",
            golden_answer="4"
        )
        
        assert question.category == "math"
        assert question.question_text == "What is 2+2?"
        assert question.golden_answer == "4"
        assert question.json_id is None
    
    def test_question_with_schema(self):
        """Test question with JSON schema"""
        schema = '{"type": "object", "properties": {"answer": {"type": "number"}}}'
        question = Question(
            category="math",
            question_text="What is 2+2?",
            answer_schema=schema
        )
        
        assert question.has_schema is True
        assert question.parsed_schema is not None
    
    def test_invalid_category_raises_error(self):
        """Test that empty category raises validation error"""
        with pytest.raises(ValueError, match="Category cannot be empty"):
            Question(category="", question_text="Test")
```

#### Integration Tests
```python
# tests/integration/test_database.py
import pytest
from src.database.connection import get_db_session
from src.database.models import Question, Response

class TestDatabaseIntegration:
    """Test database integration scenarios"""
    
    def test_question_response_relationship(self, test_db):
        """Test question-response relationship"""
        with get_db_session() as db:
            # Create question
            question = Question(
                category="test",
                question_text="Test question"
            )
            db.add(question)
            db.flush()
            
            # Create response
            response = Response(
                question_id=question.id,
                model_name="test-model",
                answer="Test answer",
                model_config='{"model": "test-model"}'
            )
            db.add(response)
            db.commit()
            
            # Verify relationship
            retrieved_question = db.query(Question).filter(
                Question.id == question.id
            ).first()
            
            assert len(retrieved_question.responses) == 1
            assert retrieved_question.responses[0].answer == "Test answer"
```

#### E2E Tests
```python
# tests/e2e/test_workflows.py
import pytest
import tempfile
import os
from click.testing import CliRunner
from src.main import cli

class TestEndToEndWorkflows:
    """Test complete user workflows"""
    
    def test_csv_import_to_export_workflow(self):
        """Test complete CSV import to export workflow"""
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("category,question,answer_schema\n")
            f.write("math,What is 2+2?,{\"answer\": \"number\"}\n")
            csv_path = f.name
        
        try:
            # Import CSV
            import_result = runner.invoke(cli, [
                'import', 'csv', csv_path,
                '--default-correct', 'null'
            ])
            assert import_result.exit_code == 0
            
            # Export data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                export_path = f.name
            
            export_result = runner.invoke(cli, [
                'export', '--output', export_path
            ])
            assert export_result.exit_code == 0
            
            # Verify export
            with open(export_path, 'r') as f:
                exported_data = f.read()
                assert "What is 2+2?" in exported_data
            
        finally:
            os.unlink(csv_path)
            os.unlink(export_path)
```

### Test Data Management

#### Fixtures
```python
# tests/conftest.py
import pytest
import tempfile
import json
from src.database.models import Question

@pytest.fixture
def sample_question_data():
    """Sample question data for testing"""
    return {
        "category": "math",
        "question_text": "What is 2+2?",
        "golden_answer": "4",
        "answer_schema": json.dumps({
            "type": "object",
            "properties": {
                "answer": {"type": "number"}
            }
        })
    }

@pytest.fixture
def sample_csv_file():
    """Temporary CSV file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("category,question,answer_schema\n")
        f.write("math,What is 2+2?,{\"answer\": \"number\"}\n")
        f.write("science,What is H2O?,{\"answer\": \"string\"}\n")
        yield f.name
    
    os.unlink(f.name)

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {
        "content": "The answer is 4.",
        "model": "gpt-3.5-turbo",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }
```

## 📏 Code Standards

### Python Code Style

#### Formatting (Black)
```bash
# Install black
pip install black

# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

#### Import Sorting (isort)
```bash
# Install isort
pip install isort

# Sort imports
isort src/ tests/

# Check import sorting
isort --check-only src/ tests/
```

#### Linting (flake8)
```bash
# Install flake8
pip install flake8

# Run linting
flake8 src/ tests/

# Configuration in setup.cfg or .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
```

#### Type Checking (mypy)
```bash
# Install mypy
pip install mypy

# Run type checking
mypy src/

# Configuration in mypy.ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### Code Quality Guidelines

#### Function Documentation
```python
def process_question(question_id: int, provider_name: str) -> Optional[Response]:
    """
    Process a single question using the specified LLM provider.
    
    Args:
        question_id: The ID of the question to process
        provider_name: The name of the LLM provider to use
        
    Returns:
        The generated response, or None if processing failed
        
    Raises:
        ValueError: If the question or provider doesn't exist
        ProviderError: If the LLM provider encounters an error
        
    Example:
        >>> response = process_question(123, "openai_main")
        >>> print(response.content)
        "The answer is 4."
    """
    pass
```

#### Class Documentation
```python
class QuestionImporter:
    """
    Import questions from various data sources.
    
    This class provides a unified interface for importing questions from
    CSV, JSON, XML, and database sources. It handles validation,
    transformation, and storage of question data.
    
    Attributes:
        config: Import configuration settings
        validator: Data validator instance
        storage: Database storage handler
        
    Example:
        >>> importer = QuestionImporter(config)
        >>> result = importer.import_from_csv("questions.csv")
        >>> print(f"Imported {result.success_count} questions")
    """
    
    def __init__(self, config: ImportConfig):
        """Initialize the importer with configuration."""
        pass
```

#### Error Handling
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class QuestionProcessor:
    def process_question(self, question_id: int) -> Optional[Response]:
        """Process question with comprehensive error handling."""
        try:
            question = self.get_question(question_id)
            if not question:
                logger.warning(f"Question {question_id} not found")
                return None
            
            response = self.generate_response(question)
            self.validate_response(response)
            self.store_response(response)
            
            logger.info(f"Successfully processed question {question_id}")
            return response
            
        except ValidationError as e:
            logger.error(f"Validation failed for question {question_id}: {e}")
            self.store_invalid_response(question_id, str(e))
            return None
            
        except ProviderError as e:
            logger.error(f"Provider error for question {question_id}: {e}")
            raise  # Re-raise for retry logic
            
        except Exception as e:
            logger.exception(f"Unexpected error processing question {question_id}")
            return None
```

## 🔄 Pull Request Process

### PR Template
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code completed
- [ ] Documentation updated if necessary
- [ ] Tests added for new functionality
- [ ] No breaking changes without proper version bump

## Issues Fixed
Closes #123
Fixes #456

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional information about the changes.
```

### PR Review Guidelines

#### Reviewer Checklist
- [ ] Code follows style guidelines
- [ ] Tests are adequate and pass
- [ ] Documentation is updated
- [ ] Breaking changes are properly documented
- [ ] Security implications considered
- [ ] Performance impact assessed
- [ ] Error handling is appropriate
- [ ] Logging is adequate

#### Author Responsibilities
- [ ] Address all reviewer comments
- [ ] Update tests based on feedback
- [ ] Update documentation based on feedback
- [ ] Ensure CI passes
- [ ] Respond to all review comments

## 🐛 Bug Reporting

### Bug Report Template
```markdown
## Bug Description
Clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Environment
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.9.7]
- LLM Distiller version: [e.g. 1.0.0]
- LLM Provider: [e.g. OpenAI GPT-4]

## Configuration
```json
{
  "llm_providers": {
    "openai": {
      "type": "openai",
      "model": "gpt-4"
    }
  }
}
```

## Logs
```
Paste relevant log output here
```

## Additional Context
Add any other context about the problem here.
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear and concise description of the feature you'd like to see added.

## Problem Statement
What problem does this feature solve? What pain point does it address?

## Proposed Solution
Describe the solution you'd like to see implemented.

## Alternatives Considered
Describe any alternative solutions or features you've considered.

## Additional Context
Add any other context, mockups, or examples about the feature request.
```

## 📚 Documentation Standards

### Documentation Types
- **API Documentation**: Code-level documentation
- **User Documentation**: End-user guides and tutorials
- **Developer Documentation**: Architecture and contribution guides
- **Examples**: Practical usage examples

### Documentation Guidelines
- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Use consistent formatting
- Include troubleshooting sections

### Documentation Review
- Technical accuracy
- Clarity and completeness
- Example functionality
- Consistency with other documentation

## 🏆 Recognition

### Contributor Recognition
- Contributors listed in README.md
- Release notes mention significant contributors
- Community highlights in project updates

### Types of Contributions
- **Code contributions**: Features, fixes, tests
- **Documentation**: Guides, examples, API docs
- **Community support**: Answering questions, triaging issues
- **Design**: UI/UX improvements, architecture input

---

*Bedankt voor je interesse in bijdragen aan de LLM Distiller! Samen kunnen we een krachtig tool bouwen voor de community.*