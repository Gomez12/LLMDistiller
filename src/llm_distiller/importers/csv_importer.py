"""CSV data importer."""

import csv
import os
from typing import List, Optional

from .base import BaseImporter, ImportResult, QuestionData


class CSVImporter(BaseImporter):
    """CSV file importer."""

    def __init__(self, db_manager, default_correct: Optional[bool] = None):
        """Initialize CSV importer.

        Args:
            db_manager: Database manager instance
            default_correct: Default correctness value for responses
        """
        self.db_manager = db_manager
        self.default_correct = default_correct

    async def validate_source(self, source: str) -> bool:
        """Validate if CSV file is accessible and valid.

        Args:
            source: Path to CSV file

        Returns:
            True if file is valid and accessible
        """
        if not os.path.exists(source):
            return False

        if not source.lower().endswith(".csv"):
            return False

        try:
            with open(source, "r", encoding="utf-8") as f:
                # Try to read first line to validate CSV format
                csv.reader(f)
                return True
        except Exception:
            return False

    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract and normalize data from CSV file.

        Args:
            source: Path to CSV file

        Returns:
            List of normalized question data
        """
        questions = []

        with open(source, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, 1):
                try:
                    # Map CSV columns to question data
                    question_data = QuestionData(
                        json_id=row.get("json_id") or row.get("id"),
                        category=row.get("category", "general"),
                        question_text=row.get("question") or row.get("question_text"),
                        golden_answer=row.get("golden_answer") or row.get("answer"),
                        answer_schema=row.get("answer_schema") or row.get("schema"),
                        system_prompt=row.get("system_prompt") or row.get("system_prompt") or row.get("prompt"),
                        default_correct=self.default_correct,
                        metadata={"row_number": row_num, "source_file": source},
                    )

                    # Validate required fields
                    if not question_data.question_text:
                        continue

                    questions.append(question_data)

                except Exception as e:
                    # Log error but continue processing other rows
                    print(f"Error processing row {row_num}: {e}")
                    continue

        return questions

    async def store_data(self, data: List[QuestionData]) -> ImportResult:
        """Store extracted data in database.

        Args:
            data: List of question data to store

        Returns:
            Import result with statistics
        """
        imported_count = 0
        error_count = 0
        errors = []

        async with self.db_manager.async_session_scope() as session:
            for question_data in data:
                try:
                    # Check if question already exists
                    existing = None
                    if question_data.json_id:
                        from ..database.models import Question

                        existing = (
                            session.query(Question)
                            .filter(Question.json_id == question_data.json_id)
                            .first()
                        )

                    if existing:
                        error_count += 1
                        errors.append(
                            f"Question with json_id '{question_data.json_id}' already exists"
                        )
                        continue

                    # Create new question
                    from ..database.models import Question

                    question = Question(
                        json_id=question_data.json_id,
                        category=question_data.category,
                        question_text=question_data.question_text,
                        golden_answer=question_data.golden_answer,
                        answer_schema=question_data.answer_schema,
                        system_prompt=question_data.system_prompt,
                        default_correct=question_data.default_correct,
                    )

                    session.add(question)
                    imported_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(f"Error storing question: {str(e)}")

        return ImportResult(
            success=error_count == 0,
            imported_count=imported_count,
            error_count=error_count,
            errors=errors,
        )
