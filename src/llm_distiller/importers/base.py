"""Base importer interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..database.models import Question


class QuestionData:
    """Normalized question data structure."""

    def __init__(
        self,
        json_id: Optional[str] = None,
        category: Optional[str] = None,
        question_text: Optional[str] = None,
        golden_answer: Optional[str] = None,
        answer_schema: Optional[str] = None,
        default_correct: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.json_id = json_id
        self.category = category
        self.question_text = question_text
        self.golden_answer = golden_answer
        self.answer_schema = answer_schema
        self.default_correct = default_correct
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<QuestionData(category='{self.category}', json_id='{self.json_id}')>"


class ImportResult:
    """Result of an import operation."""

    def __init__(
        self,
        success: bool,
        imported_count: int = 0,
        error_count: int = 0,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.imported_count = imported_count
        self.error_count = error_count
        self.errors = errors or []
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"<ImportResult(success={self.success}, imported={self.imported_count})>"


class BaseImporter(ABC):
    """Abstract base class for all data importers."""

    @abstractmethod
    async def validate_source(self, source: str) -> bool:
        """Validate if source is accessible and valid.

        Args:
            source: Source path or identifier

        Returns:
            True if source is valid and accessible
        """

    @abstractmethod
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract and normalize data from source.

        Args:
            source: Source path or identifier

        Returns:
            List of normalized question data
        """

    @abstractmethod
    async def store_data(self, data: List[QuestionData]) -> ImportResult:
        """Store extracted data in database.

        Args:
            data: List of question data to store

        Returns:
            Import result with statistics
        """

    async def import_data(self, source: str) -> ImportResult:
        """Complete import process.

        Args:
            source: Source path or identifier

        Returns:
            Import result with statistics
        """
        # Validate source
        if not await self.validate_source(source):
            return ImportResult(
                success=False, errors=[f"Source validation failed: {source}"]
            )

        # Extract data
        try:
            data = await self.extract_data(source)
        except Exception as e:
            return ImportResult(
                success=False, errors=[f"Data extraction failed: {str(e)}"]
            )

        # Store data
        return await self.store_data(data)
