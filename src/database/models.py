"""Database models for LLM Distiller."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base


class Question(Base):
    """Question entity with relationships."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    json_id = Column(String(255), unique=True, nullable=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    golden_answer = Column(Text, nullable=True)
    answer_schema = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    responses = relationship(
        "Response", back_populates="question", cascade="all, delete-orphan"
    )
    invalid_responses = relationship(
        "InvalidResponse", back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, category='{self.category}', json_id='{self.json_id}')>"


class Response(Base):
    """Valid LLM responses."""

    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, index=True
    )
    provider_name = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)  # Model reasoning/thinking process
    is_correct = Column(Boolean, nullable=True)  # NULL = not manually validated
    tokens_used = Column(Integer, nullable=True)
    cost = Column(
        Integer, nullable=True
    )  # Cost in smallest currency unit (e.g., cents)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    question = relationship("Question", back_populates="responses")

    # Constraints
    __table_args__ = (
        UniqueConstraint("question_id", "provider_name", name="uq_question_provider"),
    )

    def __repr__(self) -> str:
        return f"<Response(id={self.id}, question_id={self.question_id}, provider='{self.provider_name}')>"


class InvalidResponse(Base):
    """Invalid LLM responses that failed schema validation."""

    __tablename__ = "invalid_responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, index=True
    )
    provider_name = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    response_text = Column(Text, nullable=False)
    thinking = Column(Text, nullable=True)  # Model reasoning/thinking process
    error_message = Column(Text, nullable=False)
    error_type = Column(
        String(50), nullable=False
    )  # e.g., "schema_validation", "api_error"
    tokens_used = Column(Integer, nullable=True)
    cost = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    question = relationship("Question", back_populates="invalid_responses")

    def __repr__(self) -> str:
        return f"<InvalidResponse(id={self.id}, question_id={self.question_id}, error_type='{self.error_type}')>"
