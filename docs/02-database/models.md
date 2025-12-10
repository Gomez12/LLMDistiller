# SQLAlchemy Models

Dit document beschrijft de SQLAlchemy model classes die de database tabellen implementeren, inclusief relationships, methods en query patterns.

## 📋 Overzicht

De models zijn georganiseerd in logische groepen:
- **Base Models**: Gedeelde functionaliteit en mixins
- **Core Models**: Questions, Responses, InvalidResponses
- **Utility Models**: Helper classes en enums

## 🏗️ Base Infrastructure

### Base Model Class
```python
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

Base = declarative_base()

class TimestampMixin:
    """Mixin for timestamp functionality"""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

class BaseModel(Base, TimestampMixin):
    """Base model with common functionality"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        return cls.__name__.lower() + 's'
    
    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
```

### Enums and Constants
```python
from enum import Enum

class ValidationErrorType(str, Enum):
    """Types of validation errors"""
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DATA_TYPE = "INVALID_DATA_TYPE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

class ResponseStatus(str, Enum):
    """Response validation status"""
    VALID = "valid"
    INVALID = "invalid"
    UNVALIDATED = "unvalidated"
```

## 📝 Core Models

### Question Model
```python
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, validates
import json

class Question(BaseModel):
    """Question entity with relationships to responses"""
    
    __tablename__ = "questions"
    
    # Core fields
    json_id = Column(String(255), unique=True, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    golden_answer = Column(Text, nullable=True)
    answer_schema = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    responses = relationship("Response", back_populates="question", 
                           cascade="all, delete-orphan")
    invalid_responses = relationship("InvalidResponse", back_populates="question",
                                   cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('json_id', name='unique_json_id'),
        Index('idx_questions_category', 'category'),
        Index('idx_questions_json_id', 'json_id'),
        Index('idx_questions_created_at', 'created_at'),
    )
    
    # Validation
    @validates('category')
    def validate_category(self, key, category):
        if not category or len(category.strip()) == 0:
            raise ValueError("Category cannot be empty")
        return category.strip()
    
    @validates('question_text')
    def validate_question_text(self, key, question_text):
        if not question_text or len(question_text.strip()) == 0:
            raise ValueError("Question text cannot be empty")
        return question_text.strip()
    
    # Properties
    @property
    def has_schema(self) -> bool:
        """Check if question has answer schema"""
        return self.answer_schema is not None and len(self.answer_schema.strip()) > 0
    
    @property
    def parsed_schema(self) -> dict:
        """Parse JSON schema if present"""
        if not self.has_schema:
            return None
        try:
            return json.loads(self.answer_schema)
        except json.JSONDecodeError:
            return None
    
    @property
    def response_count(self) -> int:
        """Total number of responses (valid + invalid)"""
        return len(self.responses) + len(self.invalid_responses)
    
    @property
    def valid_response_count(self) -> int:
        """Number of valid responses"""
        return len(self.responses)
    
    @property
    def invalid_response_count(self) -> int:
        """Number of invalid responses"""
        return len(self.invalid_responses)
    
    @property
    def validated_response_count(self) -> int:
        """Number of manually validated responses"""
        return len([r for r in self.responses if r.is_correct is not None])
    
    # Methods
    def get_best_response(self) -> 'Response':
        """Get the best validated response"""
        validated = [r for r in self.responses if r.is_correct is True]
        if validated:
            return validated[0]  # Return first correct response
        return self.responses[0] if self.responses else None
    
    def get_responses_by_model(self, model_name: str) -> List['Response']:
        """Get all responses from a specific model"""
        return [r for r in self.responses if r.model_name == model_name]
    
    def has_response_from_model(self, model_name: str) -> bool:
        """Check if question has response from specific model"""
        return any(r.model_name == model_name for r in self.responses)
    
    def get_unprocessed_models(self, available_models: List[str]) -> List[str]:
        """Get models that haven't processed this question"""
        processed_models = {r.model_name for r in self.responses}
        return [m for m in available_models if m not in processed_models]
```

### Response Model
```python
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
import json

class Response(BaseModel):
    """Valid LLM response with validation status"""
    
    __tablename__ = "responses"
    
    # Foreign keys
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    
    # Core fields
    model_name = Column(String(100), nullable=False)
    model_config = Column(Text, nullable=False)  # JSON string
    reasoning = Column(Text, nullable=True)
    answer = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)  # Model reasoning/thinking process
    is_correct = Column(Boolean, nullable=True, index=True)  # NULL = unvalidated
    
    # Relationships
    question = relationship("Question", back_populates="responses")
    
    # Constraints
    __table_args__ = (
        Index('idx_responses_question_model', 'question_id', 'model_name'),
        Index('idx_responses_created_at', 'created_at'),
        Index('idx_responses_is_correct', 'is_correct'),
    )
    
    # Validation
    @validates('model_name')
    def validate_model_name(self, key, model_name):
        if not model_name or len(model_name.strip()) == 0:
            raise ValueError("Model name cannot be empty")
        return model_name.strip()
    
    @validates('answer')
    def validate_answer(self, key, answer):
        if not answer or len(answer.strip()) == 0:
            raise ValueError("Answer cannot be empty")
        return answer.strip()
    
    # Properties
    @property
    def parsed_config(self) -> dict:
        """Parse model configuration JSON"""
        try:
            return json.loads(self.model_config)
        except json.JSONDecodeError:
            return {}
    
    @property
    def parsed_answer(self) -> dict:
        """Parse answer as JSON if possible"""
        try:
            return json.loads(self.answer)
        except json.JSONDecodeError:
            return {"text": self.answer}
    
    @property
    def validation_status(self) -> ResponseStatus:
        """Get validation status"""
        if self.is_correct is True:
            return ResponseStatus.VALID
        elif self.is_correct is False:
            return ResponseStatus.INVALID
        else:
            return ResponseStatus.UNVALIDATED
    
    @property
    def is_validated(self) -> bool:
        """Check if response has been manually validated"""
        return self.is_correct is not None
    
    # Methods
    def validate_against_schema(self) -> tuple[bool, str]:
        """Validate response against question schema"""
        if not self.question or not self.question.has_schema:
            return True, "No schema to validate against"
        
        try:
            answer_data = json.loads(self.answer)
            schema = self.question.parsed_schema
            
            import jsonschema
            jsonschema.validate(answer_data, schema)
            return True, "Validation successful"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except jsonschema.ValidationError as e:
            return False, f"Schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def mark_correct(self, correct: bool = True):
        """Mark response as correct/incorrect"""
        self.is_correct = correct
    
    def get_provider_name(self) -> str:
        """Extract provider name from config"""
        config = self.parsed_config
        return config.get('provider', 'unknown')
    
    def get_model_parameters(self) -> dict:
        """Get model generation parameters"""
        config = self.parsed_config
        return {
            'temperature': config.get('temperature'),
            'max_tokens': config.get('max_tokens'),
            'top_p': config.get('top_p'),
            'frequency_penalty': config.get('frequency_penalty'),
            'presence_penalty': config.get('presence_penalty')
        }
```

### InvalidResponse Model
```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship, validates

class InvalidResponse(BaseModel):
    """Invalid LLM response with error details"""
    
    __tablename__ = "invalid_responses"
    
    # Foreign keys
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), 
                        nullable=False, index=True)
    
    # Core fields
    model_name = Column(String(100), nullable=False)
    model_config = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    answer = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)  # Model reasoning/thinking process
    validation_error = Column(Text, nullable=False)
    error_type = Column(String(50), nullable=False, index=True)
    
    # Relationships
    question = relationship("Question", back_populates="invalid_responses")
    
    # Constraints
    __table_args__ = (
        Index('idx_invalid_responses_error_type', 'error_type'),
        Index('idx_invalid_responses_created_at', 'created_at'),
    )
    
    # Validation
    @validates('error_type')
    def validate_error_type(self, key, error_type):
        valid_types = [e.value for e in ValidationErrorType]
        if error_type not in valid_types:
            raise ValueError(f"Invalid error type: {error_type}")
        return error_type
    
    # Properties
    @property
    def parsed_config(self) -> dict:
        """Parse model configuration JSON"""
        try:
            return json.loads(self.model_config)
        except json.JSONDecodeError:
            return {}
    
    @property
    def is_json_error(self) -> bool:
        """Check if error is JSON parsing related"""
        return self.error_type == ValidationErrorType.JSON_PARSE_ERROR
    
    @property
    def is_schema_error(self) -> bool:
        """Check if error is schema validation related"""
        return self.error_type == ValidationErrorType.SCHEMA_VALIDATION_ERROR
    
    # Methods
    def can_retry(self) -> bool:
        """Check if this response can be retried"""
        # JSON parsing errors might be retryable
        # Schema errors might indicate schema issues
        return self.is_json_error
    
    def get_error_summary(self) -> str:
        """Get concise error summary"""
        if len(self.validation_error) > 100:
            return self.validation_error[:97] + "..."
        return self.validation_error
```

## 🔧 Query Patterns en Methods

### Custom Query Methods
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

class QuestionRepository:
    """Repository pattern for Question queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_unprocessed_questions(self, limit: int = 100) -> List[Question]:
        """Get questions without responses"""
        return self.db.query(Question).outerjoin(Response).filter(
            Response.id.is_(None)
        ).order_by(Question.created_at).limit(limit).all()
    
    def get_questions_by_category(self, category: str) -> List[Question]:
        """Get questions by category"""
        return self.db.query(Question).filter(
            Question.category == category
        ).order_by(Question.created_at).all()
    
    def get_questions_with_schema(self) -> List[Question]:
        """Get questions that have answer schema"""
        return self.db.query(Question).filter(
            Question.answer_schema.isnot(None),
            func.trim(Question.answer_schema) != ''
        ).all()
    
    def search_questions(self, query: str, category: str = None) -> List[Question]:
        """Search questions by text"""
        base_query = self.db.query(Question).filter(
            Question.question_text.contains(query)
        )
        
        if category:
            base_query = base_query.filter(Question.category == category)
        
        return base_query.order_by(Question.created_at).all()

class ResponseRepository:
    """Repository pattern for Response queries"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_question_and_model(self, question_id: int, model_name: str) -> Response:
        """Get specific response by question and model"""
        return self.db.query(Response).filter(
            and_(Response.question_id == question_id, Response.model_name == model_name)
        ).first()
    
    def get_validated_responses(self, correct_only: bool = True) -> List[Response]:
        """Get manually validated responses"""
        query = self.db.query(Response).filter(Response.is_correct.isnot(None))
        
        if correct_only:
            query = query.filter(Response.is_correct == True)
        
        return query.order_by(desc(Response.created_at)).all()
    
    def get_model_statistics(self, model_name: str = None) -> dict:
        """Get response statistics by model"""
        base_query = self.db.query(Response)
        
        if model_name:
            base_query = base_query.filter(Response.model_name == model_name)
        
        total = base_query.count()
        correct = base_query.filter(Response.is_correct == True).count()
        incorrect = base_query.filter(Response.is_correct == False).count()
        unvalidated = base_query.filter(Response.is_correct.is_(None)).count()
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'unvalidated': unvalidated,
            'accuracy': correct / total if total > 0 else 0
        }
```

## 🔄 Database Operations

### Session Management
```python
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

@contextmanager
def get_db_session(engine):
    """Context manager for database sessions"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage
with get_db_session(engine) as db:
    question = Question(category="test", question_text="What is 2+2?")
    db.add(question)
    db.flush()  # Get ID without committing
```

### Bulk Operations
```python
def bulk_import_questions(db: Session, questions_data: List[dict]) -> dict:
    """Bulk import questions with error handling"""
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Use bulk_insert_mappings for performance
        db.bulk_insert_mappings(Question, questions_data)
        db.commit()
        success_count = len(questions_data)
    except Exception as e:
        db.rollback()
        error_count = len(questions_data)
        errors.append(str(e))
    
    return {
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors
    }
```

---

*Deze SQLAlchemy models bieden een robuuste basis voor data operaties, met duidelijke relationships, validation en query patterns die de ontwikkeling vereenvoudigen.*