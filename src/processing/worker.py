"""Question worker for processing individual questions."""

import asyncio
import json
import time
from typing import Optional

from ..database.models import InvalidResponse, Question, Response
from ..validators.schema_validator import SchemaValidator
from .manager import LLMProviderManager
from .models import QuestionTask, WorkerResult


class QuestionWorker:
    """Worker for processing individual questions."""
    
    def __init__(
        self, 
        provider_manager: LLMProviderManager,
        db_manager,
        validate_responses: bool = True
    ):
        """Initialize the question worker.
        
        Args:
            provider_manager: LLM provider manager
            db_manager: Database manager for storing results
            validate_responses: Whether to validate responses against schema
        """
        self.provider_manager = provider_manager
        self.db_manager = db_manager
        self.validate_responses = validate_responses
        self.schema_validator = SchemaValidator() if validate_responses else None
    
    async def process_question(self, task: QuestionTask) -> WorkerResult:
        """Process a single question.
        
        Args:
            task: Question task to process
            
        Returns:
            WorkerResult with processing outcome
        """
        start_time = time.time()
        
        try:
            # Generate response using LLM
            result = await self.provider_manager.generate_response_with_failover(
                prompt=task.question_text,
                preferred_provider=task.provider_name
            )
            
            # Set question ID
            result.question_id = task.question_id
            
            if not result.success:
                # Store as invalid response
                await self._store_invalid_response(task, result)
                return result
            
            # Validate response if schema validation is enabled
            validation_errors = None
            if self.validate_responses and task.answer_schema:
                validation_errors = await self._validate_response(
                    result.response_text, task.answer_schema
                )
                
                if validation_errors:
                    # Store as invalid response due to schema validation failure
                    invalid_result = WorkerResult(
                        question_id=task.question_id,
                        provider_name=result.provider_name,
                        model_name=result.model_name,
                        success=False,
                        response_text=result.response_text,
                        error_message="Schema validation failed",
                        error_type="schema_validation",
                        validation_errors=validation_errors,
                        tokens_used=result.tokens_used,
                        processing_time_ms=result.processing_time_ms
                    )
                    await self._store_invalid_response(task, invalid_result)
                    return invalid_result
            
            # Store valid response
            await self._store_valid_response(task, result)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            result.processing_time_ms = processing_time
            
            return result
            
        except Exception as e:
            # Handle unexpected errors
            error_result = WorkerResult(
                question_id=task.question_id,
                provider_name=task.provider_name or "unknown",
                model_name="unknown",
                success=False,
                error_message=str(e),
                error_type="processing_error",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            
            await self._store_invalid_response(task, error_result)
            return error_result
    
    async def _validate_response(
        self, 
        response_text: str, 
        schema_json: str
    ) -> Optional[list]:
        """Validate response against JSON schema.
        
        Args:
            response_text: Response text to validate
            schema_json: JSON schema as string
            
        Returns:
            List of validation errors, or None if valid
        """
        try:
            schema = json.loads(schema_json)
            if self.schema_validator:
                validation_result = self.schema_validator.validate_response(
                    response_text, schema
                )
                
                if validation_result.is_valid:
                    return None
                else:
                    return validation_result.errors
            else:
                return None  # Skip validation if no validator
                
        except json.JSONDecodeError:
            return ["Invalid JSON schema"]
        except Exception as e:
            return [f"Validation error: {str(e)}"]
    
    async def _store_valid_response(self, task: QuestionTask, result: WorkerResult) -> None:
        """Store a valid response in the database.
        
        Args:
            task: Original question task
            result: Processing result
        """
        async with self.db_manager.async_session_scope() as session:
            response = Response(
                question_id=task.question_id,
                provider_name=result.provider_name,
                model_name=result.model_name,
                response_text=result.response_text,
                tokens_used=result.tokens_used,
                processing_time_ms=result.processing_time_ms,
                # Cost calculation would go here if implemented
            )
            
            session.add(response)
            # session.commit() is handled by the context manager
    
    async def _store_invalid_response(self, task: QuestionTask, result: WorkerResult) -> None:
        """Store an invalid response in the database.
        
        Args:
            task: Original question task
            result: Processing result with error details
        """
        async with self.db_manager.async_session_scope() as session:
            invalid_response = InvalidResponse(
                question_id=task.question_id,
                provider_name=result.provider_name,
                model_name=result.model_name,
                response_text=result.response_text or "",
                error_message=result.error_message or "Unknown error",
                error_type=result.error_type or "unknown",
                tokens_used=result.tokens_used,
                processing_time_ms=result.processing_time_ms,
            )
            
            session.add(invalid_response)
            # session.commit() is handled by context manager
    
    def get_worker_stats(self) -> dict:
        """Get worker statistics.
        
        Returns:
            Dictionary with worker statistics
        """
        return {
            "validate_responses": self.validate_responses,
            "schema_validator_available": self.schema_validator is not None,
            "available_providers": self.provider_manager.get_available_providers(),
        }