"""Question queue for processing tasks."""

import asyncio
from typing import List, Optional, Set

from .models import ProcessingStatus, QuestionTask


class QuestionQueue:
    """Thread-safe queue for managing question processing tasks."""
    
    def __init__(self):
        """Initialize the question queue."""
        self._queue: asyncio.Queue[QuestionTask] = asyncio.Queue()
        self._processing: Set[int] = set()  # question_ids currently being processed
        self._completed: Set[int] = set()   # question_ids completed
        self._failed: Set[int] = set()      # question_ids failed
        self._tasks: dict[int, QuestionTask] = {}  # All tasks by ID
        self._lock = asyncio.Lock()
    
    async def add_task(self, task: QuestionTask) -> None:
        """Add a task to the queue."""
        async with self._lock:
            self._tasks[task.question_id] = task
            if task.status == ProcessingStatus.PENDING:
                await self._queue.put(task)
    
    async def add_tasks(self, tasks: List[QuestionTask]) -> None:
        """Add multiple tasks to the queue."""
        async with self._lock:
            for task in tasks:
                self._tasks[task.question_id] = task
                if task.status == ProcessingStatus.PENDING:
                    await self._queue.put(task)
    
    async def get_next_task(self) -> Optional[QuestionTask]:
        """Get the next task to process."""
        try:
            task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            async with self._lock:
                task.status = ProcessingStatus.PROCESSING
                self._processing.add(task.question_id)
            return task
        except asyncio.TimeoutError:
            return None
    
    async def mark_completed(self, question_id: int, success: bool = True) -> None:
        """Mark a task as completed or failed."""
        async with self._lock:
            if question_id in self._processing:
                self._processing.remove(question_id)
            
            if question_id in self._tasks:
                task = self._tasks[question_id]
                if success:
                    task.status = ProcessingStatus.COMPLETED
                    self._completed.add(question_id)
                else:
                    task.status = ProcessingStatus.FAILED
                    self._failed.add(question_id)
    
    async def retry_task(self, question_id: int) -> bool:
        """Retry a failed task if retries are available."""
        async with self._lock:
            if question_id not in self._tasks:
                return False
            
            task = self._tasks[question_id]
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = ProcessingStatus.PENDING
                task.error_message = None
                
                # Remove from failed set if present
                self._failed.discard(question_id)
                
                # Re-add to queue
                await self._queue.put(task)
                return True
            return False
    
    async def get_task(self, question_id: int) -> Optional[QuestionTask]:
        """Get a task by ID."""
        async with self._lock:
            return self._tasks.get(question_id)
    
    async def get_stats(self) -> dict:
        """Get queue statistics."""
        async with self._lock:
            return {
                "pending": self._queue.qsize(),
                "processing": len(self._processing),
                "completed": len(self._completed),
                "failed": len(self._failed),
                "total": len(self._tasks)
            }
    
    async def is_empty(self) -> bool:
        """Check if queue is empty and no tasks are processing."""
        async with self._lock:
            return self._queue.empty() and len(self._processing) == 0
    
    async def get_failed_tasks(self) -> List[QuestionTask]:
        """Get all failed tasks."""
        async with self._lock:
            return [self._tasks[qid] for qid in self._failed if qid in self._tasks]
    
    async def get_pending_tasks(self) -> List[QuestionTask]:
        """Get all pending tasks."""
        async with self._lock:
            pending_tasks = []
            # Get tasks from queue without removing them
            try:
                # Create a temporary queue to peek at items
                temp_queue = asyncio.Queue()
                while not self._queue.empty():
                    task = self._queue.get_nowait()
                    pending_tasks.append(task)
                    await temp_queue.put(task)
                
                # Put items back in original queue
                while not temp_queue.empty():
                    task = temp_queue.get_nowait()
                    await self._queue.put(task)
            except asyncio.QueueEmpty:
                pass
            return pending_tasks
    
    async def clear(self) -> None:
        """Clear all tasks from the queue."""
        async with self._lock:
            # Clear the queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            # Clear tracking sets and tasks
            self._processing.clear()
            self._completed.clear()
            self._failed.clear()
            self._tasks.clear()