"""Main processing engine for LLM Distiller."""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import List, Optional

from llm_distiller.config import Settings
from llm_distiller.database.manager import DatabaseManager
from llm_distiller.database.models import Question

from .batcher import ResponseBatcher
from .manager import LLMProviderManager
from .models import (
    ProcessingResult,
    ProcessingStats,
    ProcessingStatus,
    QuestionTask,
    WorkerResult,
)
from .queue import QuestionQueue
from .worker import QuestionWorker

logger = logging.getLogger(__name__)


class ProcessingEngine:
    """Main processing engine that orchestrates question processing."""
    
    def __init__(self, db_manager, settings: Settings):
        """Initialize the processing engine.
        
        Args:
            db_manager: Database manager instance
            settings: Application settings
        """
        self.db_manager = db_manager
        self.settings = settings
        self.queue = QuestionQueue()
        self.provider_manager = LLMProviderManager(settings)
        
        # Initialize response batcher for performance
        self.response_batcher = ResponseBatcher(
            db_manager=db_manager,
            batch_size=100  # Configurable batch size
        )
        
        self.worker = QuestionWorker(
            provider_manager=self.provider_manager,
            db_manager=db_manager,
            validate_responses=settings.processing.validate_responses,
            response_batcher=self.response_batcher
        )
        self.workers: List[QuestionWorker] = []
        self._running = False
    
    async def process_questions(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        provider: Optional[str] = None,
        default_system_prompt: Optional[str] = None,
        failover_strategy: Optional[str] = None
    ) -> ProcessingResult:
        """Process questions with LLM.
        
        Args:
            category: Filter by category
            limit: Maximum number of questions to process
            provider: Specific LLM provider to use
            
        Returns:
            ProcessingResult with statistics and any errors
        """
        result = ProcessingResult(
            success=True,
            stats=ProcessingStats(),
            errors=[],
            warnings=[]
        )
        
        try:
            # Load questions from database
            questions = await self._load_questions(category, limit)
            result.stats.total_questions = len(questions)
            
            if not questions:
                result.add_warning("No questions found to process")
                return result
            
            # Log provider selection
            if provider:
                logger.info(f"Using specified provider: {provider}")
            else:
                available_providers = self.provider_manager.get_available_providers()
                if available_providers:
                    logger.info(f"No provider specified, will use load balancing across: {', '.join(available_providers)}")
                else:
                    logger.warning("No providers configured")
            
            # Create tasks and add to queue
            tasks = []
            for q in questions:
                # Use question-specific system prompt or default
                system_prompt = q['system_prompt'] or default_system_prompt
                
                task = QuestionTask(
                    question_id=q['id'],
                    category=q['category'],
                    question_text=q['question_text'],
                    golden_answer=q['golden_answer'],
                    answer_schema=q['answer_schema'],
                    system_prompt=system_prompt,
                    provider_name=provider,
                    failover_strategy=failover_strategy,
                    max_retries=self.settings.processing.max_retries
                )
                tasks.append(task)
            
            await self.queue.add_tasks(tasks)
            result.stats.start_time = datetime.utcnow()
            
            # Start processing
            try:
                await self._run_processing(result)
            except Exception as e:
                result.add_error(f"Processing loop failed: {str(e)}")
            
            result.stats.end_time = datetime.utcnow()
            result.stats.processing_time_seconds = (
                result.stats.end_time - result.stats.start_time
            ).total_seconds()
            
            # Flush any remaining batched responses
            await self.response_batcher.flush_all()
            
            # Final statistics
            await self._update_final_stats(result)
            
        except Exception as e:
            result.add_error(f"Processing failed: {str(e)}")
        
        return result
    
    async def _load_questions(
        self, 
        category: Optional[str], 
        limit: Optional[int]
    ) -> List[dict]:
        """Load questions from database with pagination to prevent memory spikes.
        
        Args:
            category: Filter by category
            limit: Maximum number of questions
            
        Returns:
            List of question dictionaries to process
        """
        all_questions = []
        batch_size = 1000  # Load questions in batches to prevent memory issues
        offset = 0
        
        while True:
            async with self.db_manager.async_session_scope() as session:
                query = session.query(Question)
                
                # Filter out questions that already have responses
                from llm_distiller.database.models import Response
                query = query.outerjoin(Response).filter(Response.id.is_(None))
                
                if category:
                    query = query.filter(Question.category == category)
                
                # Apply pagination
                batch_query = query.offset(offset).limit(batch_size)
                if limit:
                    batch_query = batch_query.limit(min(batch_size, limit - len(all_questions)))
                
                questions = batch_query.all()
                
                if not questions:
                    break
                
                # Convert to dictionaries to avoid session binding issues
                batch_dicts = [
                    {
                        'id': q.id,
                        'json_id': q.json_id,
                        'category': q.category,
                        'question_text': q.question_text,
                        'golden_answer': q.golden_answer,
                        'answer_schema': q.answer_schema,
                        'system_prompt': q.system_prompt,
                        'created_at': q.created_at,
                        'updated_at': q.updated_at
                    }
                    for q in questions
                ]
                
                all_questions.extend(batch_dicts)
                
                # Stop if we've reached the limit
                if limit and len(all_questions) >= limit:
                    all_questions = all_questions[:limit]
                    break
                
                # Move to next batch
                offset += batch_size
                
                # If we got fewer questions than batch_size, we're done
                if len(questions) < batch_size:
                    break
        
        return all_questions
    
    async def _run_processing(self, result: ProcessingResult) -> None:
        """Run the main processing loop.
        
        Args:
            result: Processing result to update
        """
        logger.info(f"[DEBUG] Starting main processing loop")
        self._running = True
        batch_size = self.settings.processing.batch_size
        logger.debug(f"[DEBUG] Creating {batch_size} worker tasks")
        
        # Create worker tasks
        worker_tasks = []
        for i in range(batch_size):
            # Create a separate worker for each thread with shared batcher
            worker = QuestionWorker(
                provider_manager=self.provider_manager,
                db_manager=self.db_manager,
                validate_responses=self.settings.processing.validate_responses,
                response_batcher=self.response_batcher
            )
            worker_task = asyncio.create_task(self._worker_loop(result, worker))
            worker_tasks.append(worker_task)
            logger.debug(f"[DEBUG] Created worker task {i}")
        
        try:
            # Wait for all tasks to be processed with timeout
            timeout = 900  # 15 minutes timeout (900 seconds)
            start_time = asyncio.get_event_loop().time()
            logger.debug(f"[DEBUG] Processing with {timeout}s timeout (15 minutes), started at {start_time}")
            
            while not await self.queue.is_empty():
                await asyncio.sleep(0.1)
                
                # Check for timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.error(f"[ERROR] Processing timeout reached after {elapsed:.2f}s")
                    result.add_warning("Processing timeout reached")
                    break
                
                # Check for failed tasks that can be retried
                logger.debug(f"[DEBUG] Checking for failed tasks to retry")
                await self._retry_failed_tasks()
        
        except Exception as e:
            logger.error(f"[ERROR] Main processing loop failed")
            logger.error(f"[ERROR] Exception type: {type(e).__name__}")
            logger.error(f"[ERROR] Exception message: {str(e)}")
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            result.add_error(f"Processing loop failed: {str(e)}")
        
        finally:
            logger.debug(f"[DEBUG] Cancelling {len(worker_tasks)} worker tasks")
            # Cancel worker tasks
            for i, task in enumerate(worker_tasks):
                logger.debug(f"[DEBUG] Cancelling worker task {i}")
                task.cancel()
            
            # Wait for tasks to finish
            logger.debug(f"[DEBUG] Waiting for worker tasks to finish")
            await asyncio.gather(*worker_tasks, return_exceptions=True)
            self._running = False
            logger.info(f"[DEBUG] Main processing loop completed")
    
    async def _worker_loop(self, result: ProcessingResult, worker: QuestionWorker) -> None:
        """Worker loop for processing questions.
        
        Args:
            result: Processing result to update
        """
        worker_id = id(self)  # Unique identifier for this worker
        logger.debug(f"[DEBUG] Starting worker loop for worker {worker_id}")
        
        while self._running:
            try:
                # Get next task from queue
                logger.debug(f"[DEBUG] Worker {worker_id} getting next task from queue")
                task = await self.queue.get_next_task()
                if not task:
                    logger.debug(f"[DEBUG] Worker {worker_id} no tasks available, continuing")
                    continue
                
                logger.debug(f"[DEBUG] Worker {worker_id} got task {task.question_id}")
                logger.debug(f"[DEBUG] Task details: {task}")
                
                # Process the question
                logger.debug(f"[DEBUG] Worker {worker_id} starting processing of question {task.question_id}")
                worker_result = await worker.process_question(task)
                logger.debug(f"[DEBUG] Worker {worker_id} completed processing of question {task.question_id}")
                logger.debug(f"[DEBUG] Worker result: {worker_result}")
                
                # Update statistics
                await self._update_stats(result, worker_result)
                
                # Mark task as completed
                logger.debug(f"[DEBUG] Worker {worker_id} marking task {task.question_id} as completed (success: {worker_result.success})")
                await self.queue.mark_completed(
                    task.question_id, 
                    worker_result.success
                )
                
            except asyncio.CancelledError:
                logger.debug(f"[DEBUG] Worker {worker_id} cancelled, breaking loop")
                break
            except Exception as e:
                logger.error(f"[ERROR] Worker {worker_id} encountered error")
                logger.error(f"[ERROR] Exception type: {type(e).__name__}")
                logger.error(f"[ERROR] Exception message: {str(e)}")
                logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
                logger.error(f"[ERROR] Current result stats: {result.stats}")
                result.add_error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loops
    
    async def _retry_failed_tasks(self) -> None:
        """Retry failed tasks that have retries available."""
        logger.debug(f"[DEBUG] Checking for failed tasks to retry")
        failed_tasks = await self.queue.get_failed_tasks()
        logger.debug(f"[DEBUG] Found {len(failed_tasks)} failed tasks")
        
        for task in failed_tasks:
            logger.debug(f"[DEBUG] Considering retry for task {task.question_id}, current retry count: {task.retry_count}")
            if await self.queue.retry_task(task.question_id):
                logger.info(f"[DEBUG] Retrying question {task.question_id} (attempt {task.retry_count})")
                logger.debug(f"[DEBUG] Task details for retry: {task}")
            else:
                logger.debug(f"[DEBUG] Not retrying task {task.question_id} - max retries reached or other reason")
    
    async def _update_stats(self, result: ProcessingResult, worker_result: WorkerResult) -> None:
        """Update processing statistics.
        
        Args:
            result: Processing result to update
            worker_result: Result from worker processing
        """
        result.stats.processed_questions += 1
        
        if worker_result.success:
            result.stats.successful_responses += 1
        else:
            result.stats.failed_responses += 1
            
            # Check if it's a validation error
            if worker_result.error_type == "schema_validation":
                result.stats.invalid_responses += 1
        
        if worker_result.tokens_used:
            result.stats.total_tokens_used += worker_result.tokens_used
        
        if worker_result.cost_cents:
            result.stats.total_cost_cents += worker_result.cost_cents
    
    async def _update_final_stats(self, result: ProcessingResult) -> None:
        """Update final statistics after processing completes.
        
        Args:
            result: Processing result to update
        """
        queue_stats = await self.queue.get_stats()
        
        # Add any remaining failed tasks to failed count
        result.stats.failed_responses += queue_stats["failed"]
    
    async def get_status(self) -> dict:
        """Get current processing status.
        
        Returns:
            Dictionary with current status
        """
        queue_stats = await self.queue.get_stats()
        provider_stats = self.provider_manager.get_provider_stats()
        
        return {
            "running": self._running,
            "queue": queue_stats,
            "providers": provider_stats,
            "worker": self.worker.get_worker_stats(),
        }
    
    async def stop_processing(self) -> None:
        """Stop the current processing operation."""
        self._running = False