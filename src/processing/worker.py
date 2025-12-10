"""Question worker for processing individual questions."""

import asyncio
import json
import logging
import time
import traceback
from typing import Optional

from llm_distiller.database.models import InvalidResponse, Question, Response
from llm_distiller.validators.schema_validator import SchemaValidator
from .manager import LLMProviderManager
from .models import QuestionTask, WorkerResult

logger = logging.getLogger(__name__)


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
        
        logger.debug(f"[DEBUG] Starting processing of question {task.question_id} with text: {task.question_text[:100]}...")
        logger.debug(f"[DEBUG] Task details - Category: {task.category}, Provider: {task.provider_name}, Max retries: {task.max_retries}")
        
        try:
            # Generate response using LLM
            logger.debug(f"[DEBUG] Calling provider manager for question {task.question_id}")
            result = await self.provider_manager.generate_response_with_failover(
                prompt=task.question_text,
                preferred_provider=task.provider_name
            )
            
            # Set question ID
            result.question_id = task.question_id
            
            # Extract thinking from response if not already present
            if not hasattr(result, 'thinking') or result.thinking is None:
                from llm_distiller.llm.base import ThinkingExtractor
                # Use the ThinkingExtractor utility
                cleaned_content, thinking = ThinkingExtractor.extract_thinking(result.response_text or "")
                result.response_text = cleaned_content
                result.thinking = thinking
            
            print("RAW RESULT:", result)

            logger.info(f"Processing question {task.question_id} with provider: {result.provider_name}")
            logger.debug(f"[DEBUG] Provider response - Success: {result.success}, Model: {result.model_name}, Tokens: {result.tokens_used}")
            if result.thinking:
                logger.debug(f"[DEBUG] Extracted thinking (first 200 chars): {result.thinking[:200]}")
            
            if not result.success:
                # Store as invalid response with verbose error logging
                logger.error(f"[ERROR] Failed to process question {task.question_id} with provider {result.provider_name}")
                logger.error(f"[ERROR] Error type: {result.error_type}")
                logger.error(f"[ERROR] Error message: {result.error_message}")
                logger.error(f"[ERROR] Processing time: {result.processing_time_ms}ms")
                logger.error(f"[ERROR] Tokens used: {result.tokens_used}")
                if result.validation_errors:
                    logger.error(f"[ERROR] Validation errors: {result.validation_errors}")
                logger.error(f"[DEBUG] Full task context: {task}")
                logger.error(f"[DEBUG] Full result context: {result}")
                
                await self._store_invalid_response(task, result)
                return result
            
            # Validate response if schema validation is enabled
            validation_errors = None
            if self.validate_responses and task.answer_schema:
                logger.debug(f"[DEBUG] Validating response for question {task.question_id} against schema")
                logger.debug(f"[DEBUG] Response text (first 200 chars): {result.response_text[:200] if result.response_text else 'None'}")
                logger.debug(f"[DEBUG] Schema: {task.answer_schema}")
                
                validation_errors = await self._validate_response(
                    result.response_text, task.answer_schema
                )
                
                if validation_errors:
                    # Store as invalid response due to schema validation failure with verbose logging
                    logger.error(f"[ERROR] Schema validation failed for question {task.question_id}")
                    logger.error(f"[ERROR] Provider: {result.provider_name}, Model: {result.model_name}")
                    logger.error(f"[ERROR] Validation errors: {validation_errors}")
                    logger.error(f"[ERROR] Response text: {result.response_text}")
                    logger.error(f"[ERROR] Schema: {task.answer_schema}")
                    
                    invalid_result = WorkerResult(
                        question_id=task.question_id,
                        provider_name=result.provider_name,
                        model_name=result.model_name,
                        success=False,
                        response_text=result.response_text,
                        thinking=getattr(result, 'thinking', None),
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
            
            logger.info(f"Successfully processed question {task.question_id} with provider {result.provider_name}")
            
            return result
            
        except Exception as e:
            # Handle unexpected errors with verbose logging
            logger.error(f"[ERROR] Unexpected error processing question {task.question_id}")
            logger.error(f"[ERROR] Exception type: {type(e).__name__}")
            logger.error(f"[ERROR] Exception message: {str(e)}")
            logger.error(f"[ERROR] Full traceback: {traceback.format_exc()}")
            logger.error(f"[ERROR] Task context: {task}")
            logger.error(f"[ERROR] Provider manager: {self.provider_manager}")
            logger.error(f"[ERROR] Processing time so far: {int((time.time() - start_time) * 1000)}ms")
            
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
        response_text: Optional[str], 
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
            logger.debug(f"[DEBUG] Starting validation of response")
            logger.debug(f"[DEBUG] Response text: {response_text}")
            logger.debug(f"[DEBUG] Schema JSON: {schema_json}")
            
            if not response_text:
                logger.error(f"[ERROR] Response text is empty during validation")
                return ["Response text is empty"]
                
            schema = json.loads(schema_json)
            logger.debug(f"[DEBUG] Parsed schema successfully: {schema}")
            
            if self.schema_validator:
                logger.debug(f"[DEBUG] Calling schema validator")
                validation_result = self.schema_validator.validate_response(
                    response_text, schema
                )
                
                logger.debug(f"[DEBUG] Validation result - Valid: {validation_result.is_valid}, Errors: {validation_result.errors}")
                
                if validation_result.is_valid:
                    logger.debug(f"[DEBUG] Validation passed")
                    return None
                else:
                    logger.error(f"[ERROR] Schema validation failed with errors: {validation_result.errors}")
                    logger.error(f"[ERROR] Response that failed: {response_text}")
                    logger.error(f"[ERROR] Schema used: {schema}")
                    return validation_result.errors
            else:
                logger.warning(f"[DEBUG] No schema validator available, skipping validation")
                return None  # Skip validation if no validator
                
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] JSON decode error during validation: {e}")
            logger.error(f"[ERROR] Invalid schema JSON: {schema_json}")
            return [f"Invalid JSON schema: {str(e)}"]
        except Exception as e:
            logger.error(f"[ERROR] Unexpected validation error: {e}")
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            logger.error(f"[ERROR] Response text: {response_text}")
            logger.error(f"[ERROR] Schema JSON: {schema_json}")
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
                thinking=result.thinking or None,
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
                thinking=result.thinking or None,
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