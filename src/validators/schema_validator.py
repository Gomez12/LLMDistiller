"""JSON schema validation system."""

import json
from typing import Any, Dict, List, Optional

import jsonschema

from ..database.models import Question, Response


class ValidationResult:
    """Result of schema validation."""

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        normalized_response: Optional[Dict[str, Any]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.normalized_response = normalized_response or {}

    def __repr__(self) -> str:
        return (
            f"<ValidationResult(is_valid={self.is_valid}, errors={len(self.errors)})>"
        )


class SchemaValidator:
    """JSON schema validation with detailed error reporting."""

    def __init__(self):
        """Initialize schema validator."""
        self.validator_class = jsonschema.Draft7Validator

    def validate_response(
        self, response: str, schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate response against JSON schema.

        Args:
            response: Response string to validate
            schema: JSON schema dictionary

        Returns:
            Validation result with errors if any
        """
        try:
            # Parse response as JSON
            response_data = json.loads(response)
        except json.JSONDecodeError as e:
            return ValidationResult(is_valid=False, errors=[f"Invalid JSON: {str(e)}"])

        return self.validate_json_data(response_data, schema)

    def validate_json_data(
        self, data: Dict[str, Any], schema: Dict[str, Any]
    ) -> ValidationResult:
        """Validate JSON data against schema.

        Args:
            data: JSON data to validate
            schema: JSON schema dictionary

        Returns:
            Validation result with errors if any
        """
        try:
            validator = self.validator_class(schema)
            errors = list(validator.iter_errors(data))

            if not errors:
                return ValidationResult(is_valid=True, normalized_response=data)

            # Format errors
            formatted_errors = []
            for error in errors:
                path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                formatted_errors.append(f"Path '{path}': {error.message}")

            return ValidationResult(is_valid=False, errors=formatted_errors)

        except jsonschema.SchemaError as e:
            return ValidationResult(
                is_valid=False, errors=[f"Invalid schema: {str(e)}"]
            )

    def get_validation_errors(self, response: str, schema: Dict[str, Any]) -> List[str]:
        """Get detailed validation error messages.

        Args:
            response: Response string to validate
            schema: JSON schema dictionary

        Returns:
            List of error messages
        """
        result = self.validate_response(response, schema)
        return result.errors

    def suggest_schema_fix(self, response: str, schema: Dict[str, Any]) -> str:
        """Suggest fixes for invalid schemas.

        Args:
            response: Response that failed validation
            schema: Current schema

        Returns:
            Suggested schema improvements
        """
        try:
            response_data = json.loads(response)
        except json.JSONDecodeError:
            return "Response is not valid JSON"

        # This is a simple implementation - in practice, you might want
        # more sophisticated schema inference
        suggestions = []

        # Check for missing required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in response_data:
                suggestions.append(f"Field '{field}' is missing from response")

        # Check for extra fields not in schema
        schema_properties = schema.get("properties", {})
        for field in response_data:
            if field not in schema_properties:
                suggestions.append(
                    f"Consider adding field '{field}' to schema properties"
                )

        return (
            "; ".join(suggestions)
            if suggestions
            else "No specific suggestions available"
        )


class QualityAssessor:
    """Assess response quality beyond schema validation."""

    def assess_response(self, question: Question, response: Response) -> float:
        """Assess overall response quality.

        Args:
            question: Question object
            response: Response object

        Returns:
            Quality score between 0.0 and 1.0
        """
        scores = []

        # Check completeness
        if question.answer_schema:
            try:
                schema = json.loads(question.answer_schema)
                completeness = self.check_completeness(response.response_text, schema)
                scores.append(completeness)
            except json.JSONDecodeError:
                pass

        # Check coherence
        coherence = self.check_coherence(question.question_text, response.response_text)
        scores.append(coherence)

        # Check length appropriateness
        length_score = self.check_length_appropriateness(response.response_text)
        scores.append(length_score)

        return sum(scores) / len(scores) if scores else 0.5

    def check_completeness(self, response: str, schema: Dict[str, Any]) -> float:
        """Check if response contains all required fields.

        Args:
            response: Response string
            schema: JSON schema

        Returns:
            Completeness score between 0.0 and 1.0
        """
        try:
            response_data = json.loads(response)
        except json.JSONDecodeError:
            return 0.0

        required_fields = schema.get("required", [])
        if not required_fields:
            return 1.0  # No required fields means complete

        present_fields = sum(1 for field in required_fields if field in response_data)
        return present_fields / len(required_fields)

    def check_coherence(self, question: str, response: str) -> float:
        """Check response coherence with question.

        Args:
            question: Question text
            response: Response text

        Returns:
            Coherence score between 0.0 and 1.0
        """
        # Simple heuristic-based coherence check
        # In practice, you might use more sophisticated NLP techniques

        question_words = set(question.lower().split())
        response_words = set(response.lower().split())

        # Check if response contains some question keywords
        overlap = len(question_words & response_words)
        question_len = len(question_words)

        if question_len == 0:
            return 0.5

        # Normalize overlap score
        overlap_score = min(overlap / question_len, 1.0)

        # Check response length (not too short, not too long)
        response_len = len(response.split())
        length_score = 1.0 if 10 <= response_len <= 500 else 0.5

        return (overlap_score + length_score) / 2

    def check_length_appropriateness(self, response: str) -> float:
        """Check if response length is appropriate.

        Args:
            response: Response text

        Returns:
            Length score between 0.0 and 1.0
        """
        word_count = len(response.split())

        # Define appropriate length ranges
        if word_count < 5:
            return 0.2  # Too short
        elif word_count > 1000:
            return 0.3  # Too long
        elif 10 <= word_count <= 200:
            return 1.0  # Ideal length
        else:
            return 0.7  # Acceptable length
