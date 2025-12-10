"""Processing data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class ProcessingStatus(Enum):
    """Processing status for questions."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingStats:
    """Statistics for processing operations."""
    total_questions: int = 0
    processed_questions: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    invalid_responses: int = 0
    total_tokens_used: int = 0
    total_cost_cents: int = 0
    processing_time_seconds: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_questions == 0:
            return 0.0
        return (self.successful_responses / self.processed_questions) * 100
    
    @property
    def average_tokens_per_question(self) -> float:
        """Calculate average tokens used per question."""
        if self.processed_questions == 0:
            return 0.0
        return self.total_tokens_used / self.processed_questions
    
    @property
    def questions_per_second(self) -> float:
        """Calculate processing speed."""
        if self.processing_time_seconds == 0:
            return 0.0
        return self.processed_questions / self.processing_time_seconds


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    success: bool
    stats: ProcessingStats
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


@dataclass
class QuestionTask:
    """Task for processing a single question."""
    question_id: int
    category: str
    question_text: str
    golden_answer: Optional[str]
    answer_schema: Optional[str]
    provider_name: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class WorkerResult:
    """Result from processing a single question."""
    question_id: int
    provider_name: str
    model_name: str
    success: bool
    response_text: Optional[str] = None
    thinking: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_cents: Optional[int] = None
    processing_time_ms: Optional[int] = None
    validation_errors: Optional[List[str]] = None