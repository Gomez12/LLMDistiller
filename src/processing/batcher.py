"""Batch processing for database operations to improve performance."""

import asyncio
import logging
from typing import List, Optional, Tuple

from llm_distiller.database.models import InvalidResponse, Question, Response

from .models import QuestionTask, WorkerResult

logger = logging.getLogger(__name__)


class ResponseBatcher:
    """Handles batch database operations for responses to improve performance."""
    
    def __init__(self, db_manager, batch_size: int = 100):
        """Initialize response batcher.
        
        Args:
            db_manager: Database manager instance
            batch_size: Number of responses to batch before writing to database
        """
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.pending_valid_responses: List[Tuple[QuestionTask, WorkerResult]] = []
        self.pending_invalid_responses: List[Tuple[QuestionTask, WorkerResult]] = []
        self._lock = asyncio.Lock()
    
    async def add_valid_response(self, task: QuestionTask, result: WorkerResult) -> None:
        """Add a valid response to the batch.
        
        Args:
            task: Original question task
            result: Processing result with valid response
        """
        async with self._lock:
            self.pending_valid_responses.append((task, result))
            
            if len(self.pending_valid_responses) >= self.batch_size:
                await self._flush_valid_responses()
    
    async def add_invalid_response(self, task: QuestionTask, result: WorkerResult) -> None:
        """Add an invalid response to the batch.
        
        Args:
            task: Original question task
            result: Processing result with error details
        """
        async with self._lock:
            self.pending_invalid_responses.append((task, result))
            
            if len(self.pending_invalid_responses) >= self.batch_size:
                await self._flush_invalid_responses()
    
    async def flush_all(self) -> None:
        """Flush all pending responses to database."""
        async with self._lock:
            if self.pending_valid_responses:
                await self._flush_valid_responses()
            if self.pending_invalid_responses:
                await self._flush_invalid_responses()
    
    async def _flush_valid_responses(self) -> None:
        """Flush valid responses to database in a single transaction."""
        if not self.pending_valid_responses:
            return
        
        logger.debug(f"Flushing {len(self.pending_valid_responses)} valid responses to database")
        
        async with self.db_manager.async_session_scope() as session:
            for task, result in self.pending_valid_responses:
                response = Response(
                    question_id=task.question_id,
                    provider_name=result.provider_name,
                    model_name=result.model_name,
                    response_text=result.response_text,
                    thinking=result.thinking or None,
                    tokens_used=result.tokens_used,
                    processing_time_ms=result.processing_time_ms,
                )
                session.add(response)
        
        logger.debug(f"Successfully flushed {len(self.pending_valid_responses)} valid responses")
        self.pending_valid_responses.clear()
    
    async def _flush_invalid_responses(self) -> None:
        """Flush invalid responses to database in a single transaction."""
        if not self.pending_invalid_responses:
            return
        
        logger.debug(f"Flushing {len(self.pending_invalid_responses)} invalid responses to database")
        
        async with self.db_manager.async_session_scope() as session:
            for task, result in self.pending_invalid_responses:
                invalid_response = InvalidResponse(
                    question_id=task.question_id,
                    provider_name=result.provider_name,
                    model_name=result.model_name,
                    response_text=result.response_text or "",
                    thinking=result.thinking or None,
                    error_message=result.error_message or "Unknown error",
                    error_type=result.error_type or "unknown",
                    tokens_used=result.tokens_used,
                    processing_time_ms=result.processing_time_ms,
                )
                session.add(invalid_response)
        
        logger.debug(f"Successfully flushed {len(self.pending_invalid_responses)} invalid responses")
        self.pending_invalid_responses.clear()
    
    def get_stats(self) -> dict:
        """Get current batch statistics.
        
        Returns:
            Dictionary with batch statistics
        """
        return {
            "pending_valid": len(self.pending_valid_responses),
            "pending_invalid": len(self.pending_invalid_responses),
            "batch_size": self.batch_size,
            "total_pending": len(self.pending_valid_responses) + len(self.pending_invalid_responses)
        }