"""Unit tests for database models."""

import pytest
from sqlalchemy.orm import Session

from llm_distiller.database.models import Question, Response, InvalidResponse


class TestQuestion:
    """Test Question model."""

    def test_question_creation(self, test_db_session: Session):
        """Test creating a question."""
        question = Question(
            json_id="test_1",
            category="math",
            question_text="What is 2+2?",
            golden_answer="4",
            answer_schema='{"type": "object", "properties": {"answer": {"type": "number"}}}',
        )
        
        test_db_session.add(question)
        test_db_session.commit()
        test_db_session.refresh(question)
        
        assert question.id is not None
        assert question.json_id == "test_1"
        assert question.category == "math"
        assert question.question_text == "What is 2+2?"
        assert question.golden_answer == "4"
        assert question.answer_schema == '{"type": "object", "properties": {"answer": {"type": "number"}}}'
        assert question.created_at is not None
        assert question.updated_at is not None

    def test_question_unique_json_id(self, test_db_session: Session):
        """Test that json_id must be unique."""
        question1 = Question(
            json_id="duplicate_id",
            category="math",
            question_text="Question 1",
            golden_answer="Answer 1",
            answer_schema='{"type": "string"}',
        )
        
        question2 = Question(
            json_id="duplicate_id",  # Same json_id
            category="science",
            question_text="Question 2",
            golden_answer="Answer 2",
            answer_schema='{"type": "string"}',
        )
        
        test_db_session.add(question1)
        test_db_session.commit()
        
        test_db_session.add(question2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db_session.commit()

    def test_question_string_representation(self, test_db_session: Session):
        """Test question string representation."""
        question = Question(
            json_id="test_1",
            category="math",
            question_text="What is 2+2?",
            golden_answer="4",
            answer_schema='{"type": "object"}',
        )
        
        test_db_session.add(question)
        test_db_session.commit()
        
        expected = f"<Question(id={question.id}, category='math', json_id='test_1')>"
        assert str(question) == expected


class TestResponse:
    """Test Response model."""

    def test_response_creation(self, test_db_session: Session, sample_questions):
        """Test creating a response."""
        # First create a question
        question = Question(
            json_id=sample_questions[0]["json_id"],
            category=sample_questions[0]["category"],
            question_text=sample_questions[0]["question"],
            golden_answer=sample_questions[0]["golden_answer"],
            answer_schema=sample_questions[0]["answer_schema"],
        )
        test_db_session.add(question)
        test_db_session.commit()
        
        # Now create a response
        response = Response(
            question_id=question.id,
            provider_name="test_provider",
            model_name="test-model",
            response_text='{"answer": "4"}',
            tokens_used=50,
            processing_time_ms=500,
            is_correct=True,
        )
        
        test_db_session.add(response)
        test_db_session.commit()
        test_db_session.refresh(response)
        
        assert response.id is not None
        assert response.question_id == question.id
        assert response.provider_name == "test_provider"
        assert response.model_name == "test-model"
        assert response.response_text == '{"answer": "4"}'
        assert response.tokens_used == 50
        assert response.processing_time_ms == 500
        assert response.is_correct is True
        assert response.created_at is not None

    def test_response_question_relationship(self, test_db_session: Session, sample_questions):
        """Test response-question relationship."""
        question = Question(
            json_id=sample_questions[0]["json_id"],
            category=sample_questions[0]["category"],
            question_text=sample_questions[0]["question"],
            golden_answer=sample_questions[0]["golden_answer"],
            answer_schema=sample_questions[0]["answer_schema"],
        )
        test_db_session.add(question)
        test_db_session.commit()
        
        response = Response(
            question_id=question.id,
            provider_name="test_provider",
            model_name="test-model",
            response_text='{"answer": "4"}',
            tokens_used=50,
            processing_time_ms=500,
        )
        test_db_session.add(response)
        test_db_session.commit()
        
        # Test relationship
        assert response.question == question
        assert question.responses == [response]


class TestInvalidResponse:
    """Test InvalidResponse model."""

    def test_invalid_response_creation(self, test_db_session: Session, sample_questions):
        """Test creating an invalid response."""
        question = Question(
            json_id=sample_questions[0]["json_id"],
            category=sample_questions[0]["category"],
            question_text=sample_questions[0]["question"],
            golden_answer=sample_questions[0]["golden_answer"],
            answer_schema=sample_questions[0]["answer_schema"],
        )
        test_db_session.add(question)
        test_db_session.commit()
        
        invalid_response = InvalidResponse(
            question_id=question.id,
            provider_name="test_provider",
            model_name="test-model",
            response_text="Invalid JSON response",
            error_message="JSON validation failed",
            error_type="schema_validation",
            tokens_used=0,
            processing_time_ms=100,
        )
        
        test_db_session.add(invalid_response)
        test_db_session.commit()
        test_db_session.refresh(invalid_response)
        
        assert invalid_response.id is not None
        assert invalid_response.question_id == question.id
        assert invalid_response.provider_name == "test_provider"
        assert invalid_response.model_name == "test-model"
        assert invalid_response.response_text == "Invalid JSON response"
        assert invalid_response.error_message == "JSON validation failed"
        assert invalid_response.error_type == "schema_validation"
        assert invalid_response.tokens_used == 0
        assert invalid_response.processing_time_ms == 100
        assert invalid_response.created_at is not None

    def test_invalid_response_question_relationship(self, test_db_session: Session, sample_questions):
        """Test invalid response-question relationship."""
        question = Question(
            json_id=sample_questions[0]["json_id"],
            category=sample_questions[0]["category"],
            question_text=sample_questions[0]["question"],
            golden_answer=sample_questions[0]["golden_answer"],
            answer_schema=sample_questions[0]["answer_schema"],
        )
        test_db_session.add(question)
        test_db_session.commit()
        
        invalid_response = InvalidResponse(
            question_id=question.id,
            provider_name="test_provider",
            model_name="test-model",
            response_text="Invalid response",
            error_message="Error",
            error_type="api_error",
        )
        test_db_session.add(invalid_response)
        test_db_session.commit()
        
        # Test relationship
        assert invalid_response.question == question
        assert question.invalid_responses == [invalid_response]