"""Main processing engine for LLM Distiller."""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from ..config import Settings
from ..database.models import Question
from .manager import LLMProviderManager
from .models import ProcessingResult, ProcessingStats, QuestionTask, ProcessingStatus, WorkerResult
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
        self.worker = QuestionWorker(
            provider_manager=self.provider_manager,
            db_manager=db_manager,
            validate_responses=settings.processing.validate_responses
        )
        self.workers: List[QuestionWorker] = []
        self._running = False
    
    async def process_questions(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        provider: Optional[str] = None
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
                task = QuestionTask(
                    question_id=q['id'],
                    category=q['category'],
                    question_text=q['question_text'],
                    golden_answer=q['golden_answer'],
                    answer_schema=q['answer_schema'],
                    provider_name=provider,
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
        """Load questions from database.
        
        Args:
            category: Filter by category
            limit: Maximum number of questions
            
        Returns:
            List of question dictionaries to process
        """
        async with self.db_manager.async_session_scope() as session:
            query = session.query(Question)
            
            # Filter out questions that already have responses
            from ..database.models import Response
            query = query.outerjoin(Response).filter(Response.id.is_(None))
            
            if category:
                query = query.filter(Question.category == category)
            
            if limit:
                query = query.limit(limit)
            
            questions = query.all()
            
            # Convert to dictionaries to avoid session binding issues
            return [
                {
                    'id': q.id,
                    'json_id': q.json_id,
                    'category': q.category,
                    'question_text': q.question_text,
                    'golden_answer': q.golden_answer,
                    'answer_schema': q.answer_schema,
                    'created_at': q.created_at,
                    'updated_at': q.updated_at
                }
                for q in questions
            ]
    
    async def _run_processing(self, result: ProcessingResult) -> None:
        """Run the main processing loop.
        
        Args:
            result: Processing result to update
        """
        self._running = True
        batch_size = self.settings.processing.batch_size
        
        # Create worker tasks
        worker_tasks = []
        for i in range(batch_size):
            worker_task = asyncio.create_task(self._worker_loop(result))
            worker_tasks.append(worker_task)
        
        try:
            # Wait for all tasks to be processed with timeout
            timeout = 30  # 30 seconds timeout
            start_time = asyncio.get_event_loop().time()
            
            while not await self.queue.is_empty():
                await asyncio.sleep(0.1)
                
                # Check for timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    result.add_warning("Processing timeout reached")
                    break
                
                # Check for failed tasks that can be retried
                await self._retry_failed_tasks()
        
        finally:
            # Cancel worker tasks
            for task in worker_tasks:
                task.cancel()
            
            # Wait for tasks to finish
            await asyncio.gather(*worker_tasks, return_exceptions=True)
            self._running = False
    
    async def _worker_loop(self, result: ProcessingResult) -> None:
        """Worker loop for processing questions.
        
        Args:
            result: Processing result to update
        """
        while self._running:
            try:
                # Get next task from queue
                task = await self.queue.get_next_task()
                if not task:
                    continue
                
                # Process the question
                worker_result = await self.worker.process_question(task)
                
                # Update statistics
                await self._update_stats(result, worker_result)
                
                # Mark task as completed
                await self.queue.mark_completed(
                    task.question_id, 
                    worker_result.success
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                result.add_error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loops
    
    async def _retry_failed_tasks(self) -> None:
        """Retry failed tasks that have retries available."""
        failed_tasks = await self.queue.get_failed_tasks()
        
        for task in failed_tasks:
            if await self.queue.retry_task(task.question_id):
                print(f"Retrying question {task.question_id} (attempt {task.retry_count})")
    
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