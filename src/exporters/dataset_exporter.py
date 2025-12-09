"""Export functionality for LLM Distiller datasets."""

import csv
import json
from typing import List, Optional

from ..database.models import Question, Response


class DatasetExporter:
    """Export processed data in various formats for fine-tuning."""

    def __init__(self, db_manager):
        """Initialize exporter.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def export_jsonl(
        self,
        output_path: str,
        validated_only: bool = False,
        category: Optional[str] = None,
    ) -> int:
        """Export data in JSONL format.

        Args:
            output_path: Path to output file
            validated_only: Export only validated responses
            category: Filter by category

        Returns:
            Number of records exported
        """
        records = self._get_export_data(validated_only, category)

        with open(output_path, "w", encoding="utf-8") as f:
            for record in records:
                json_line = json.dumps(record, ensure_ascii=False)
                f.write(json_line + "\n")

        return len(records)

    def export_csv(
        self,
        output_path: str,
        validated_only: bool = False,
        category: Optional[str] = None,
    ) -> int:
        """Export data in CSV format.

        Args:
            output_path: Path to output file
            validated_only: Export only validated responses
            category: Filter by category

        Returns:
            Number of records exported
        """
        records = self._get_export_data(validated_only, category)

        if not records:
            return 0

        fieldnames = [
            "question_id",
            "json_id",
            "category",
            "question_text",
            "golden_answer",
            "answer_schema",
            "response_text",
            "provider_name",
            "model_name",
            "is_correct",
            "tokens_used",
            "processing_time_ms",
            "created_at",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for record in records:
                # Flatten nested structure for CSV
                row = {
                    "question_id": record.get("question", {}).get("id"),
                    "json_id": record.get("question", {}).get("json_id"),
                    "category": record.get("question", {}).get("category"),
                    "question_text": record.get("question", {}).get("question_text"),
                    "golden_answer": record.get("question", {}).get("golden_answer"),
                    "answer_schema": record.get("question", {}).get("answer_schema"),
                    "response_text": record.get("response", {}).get("response_text"),
                    "provider_name": record.get("response", {}).get("provider_name"),
                    "model_name": record.get("response", {}).get("model_name"),
                    "is_correct": record.get("response", {}).get("is_correct"),
                    "tokens_used": record.get("response", {}).get("tokens_used"),
                    "processing_time_ms": record.get("response", {}).get(
                        "processing_time_ms"
                    ),
                    "created_at": record.get("response", {}).get("created_at"),
                }
                writer.writerow(row)

        return len(records)

    def export_json(
        self,
        output_path: str,
        validated_only: bool = False,
        category: Optional[str] = None,
    ) -> int:
        """Export data in JSON format.

        Args:
            output_path: Path to output file
            validated_only: Export only validated responses
            category: Filter by category

        Returns:
            Number of records exported
        """
        records = self._get_export_data(validated_only, category)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False, default=str)

        return len(records)

    def _get_export_data(
        self,
        validated_only: bool = False,
        category: Optional[str] = None,
    ) -> List[dict]:
        """Get data for export.

        Args:
            validated_only: Include only validated responses
            category: Filter by category

        Returns:
            List of export records
        """
        with self.db_manager.session_scope() as session:
            query = session.query(Question, Response).join(Response)

            if category:
                query = query.filter(Question.category == category)

            if validated_only:
                query = query.filter(Response.is_correct == True)

            results = query.all()

            records = []
            for question, response in results:
                record = {
                    "question": {
                        "id": question.id,
                        "json_id": question.json_id,
                        "category": question.category,
                        "question_text": question.question_text,
                        "golden_answer": question.golden_answer,
                        "answer_schema": question.answer_schema,
                        "created_at": (
                            question.created_at.isoformat()
                            if question.created_at
                            else None
                        ),
                    },
                    "response": {
                        "id": response.id,
                        "provider_name": response.provider_name,
                        "model_name": response.model_name,
                        "response_text": response.response_text,
                        "is_correct": response.is_correct,
                        "tokens_used": response.tokens_used,
                        "cost": response.cost,
                        "processing_time_ms": response.processing_time_ms,
                        "created_at": (
                            response.created_at.isoformat()
                            if response.created_at
                            else None
                        ),
                    },
                }
                records.append(record)

            return records

    def get_export_summary(self) -> dict:
        """Get summary of available data for export.

        Returns:
            Summary statistics
        """
        with self.db_manager.session_scope() as session:
            total_questions = session.query(Question).count()
            total_responses = session.query(Response).count()
            validated_responses = (
                session.query(Response).filter(Response.is_correct == True).count()
            )

            # Get category breakdown
            category_stats = (
                session.query(
                    Question.category,
                    session.query(Response)
                    .join(Question)
                    .filter(Question.category == Question.category)
                    .count(),
                )
                .group_by(Question.category)
                .all()
            )

            return {
                "total_questions": total_questions,
                "total_responses": total_responses,
                "validated_responses": validated_responses,
                "validation_rate": (
                    (validated_responses / total_responses * 100)
                    if total_responses > 0
                    else 0
                ),
                "categories": dict(category_stats) if category_stats else {},
            }
