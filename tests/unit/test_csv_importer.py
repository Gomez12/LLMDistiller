"""Unit tests for CSV importer."""

import pytest
from unittest.mock import Mock, patch

from llm_distiller.importers.csv_importer import CSVImporter
from llm_distiller.database.manager import DatabaseManager


class TestCSVImporter:
    """Test CSV importer functionality."""

    @pytest.fixture
    def importer(self, test_db_manager: DatabaseManager):
        """Create CSV importer instance."""
        return CSVImporter(test_db_manager)

    @pytest.mark.asyncio
    async def test_import_valid_csv(self, importer: CSVImporter, sample_csv_file: str):
        """Test importing a valid CSV file."""
        result = await importer.import_data(sample_csv_file)
        
        assert result.success is True
        assert result.imported_count == 3
        assert result.error_count == 0
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_import_empty_csv(self, importer: CSVImporter, temp_output_dir):
        """Test importing an empty CSV file."""
        import csv
        
        empty_csv = temp_output_dir / "empty.csv"
        with open(empty_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['json_id', 'category', 'question', 'golden_answer', 'answer_schema'])
        
        result = await importer.import_data(str(empty_csv))
        
        assert result.success is True
        assert result.imported_count == 0
        assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_import_csv_with_duplicates(self, importer: CSVImporter, sample_csv_file: str):
        """Test importing CSV with duplicate json_id."""
        # First import
        result1 = await importer.import_data(sample_csv_file)
        assert result1.success is True
        assert result1.imported_count == 3
        
        # Second import (should fail on duplicates)
        result2 = await importer.import_data(sample_csv_file)
        assert result2.success is False
        assert result2.imported_count == 0
        assert result2.error_count == 3
        assert any("already exists" in error for error in result2.errors)

    @pytest.mark.asyncio
    async def test_import_csv_missing_columns(self, importer: CSVImporter, temp_output_dir):
        """Test importing CSV with missing required columns."""
        import csv
        
        invalid_csv = temp_output_dir / "invalid.csv"
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['json_id', 'category'])  # Missing required columns
            writer.writerow(['1', 'math'])
        
        result = await importer.import_data(str(invalid_csv))
        
        assert result.success is False
        assert result.imported_count == 0
        assert result.error_count > 0

    @pytest.mark.asyncio
    async def test_import_nonexistent_file(self, importer: CSVImporter):
        """Test importing a non-existent file."""
        result = await importer.import_data("nonexistent.csv")
        
        assert result.success is False
        assert result.imported_count == 0
        assert result.error_count == 1
        assert "No such file" in result.errors[0]

    @pytest.mark.asyncio
    async def test_import_malformed_csv(self, importer: CSVImporter, temp_output_dir):
        """Test importing a malformed CSV file."""
        malformed_csv = temp_output_dir / "malformed.csv"
        with open(malformed_csv, 'w') as f:
            f.write("json_id,category,question\n")
            f.write("1,math,What is 2+2\n")  # Missing closing quote
            f.write("unclosed line\n")
        
        result = await importer.import_data(str(malformed_csv))
        
        assert result.success is False
        assert result.error_count > 0

    @pytest.mark.asyncio
    async def test_import_with_validation_errors(self, importer: CSVImporter, temp_output_dir):
        """Test importing CSV with validation errors."""
        import csv
        
        invalid_csv = temp_output_dir / "validation_errors.csv"
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['json_id', 'category', 'question', 'golden_answer', 'answer_schema'])
            writer.writerow(['', 'math', 'What is 2+2?', '4', '{"type": "object"}'])  # Empty json_id
            writer.writerow(['2', '', 'What is H2O?', 'Water', '{"type": "object"}'])  # Empty category
        
        result = await importer.import_data(str(invalid_csv))
        
        assert result.success is False
        assert result.imported_count == 0
        assert result.error_count >= 2

    def test_validate_csv_structure_valid(self, importer: CSVImporter, sample_csv_file: str):
        """Test CSV structure validation with valid file."""
        import pandas as pd
        
        df = pd.read_csv(sample_csv_file)
        is_valid, errors = importer._validate_csv_structure(df)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_csv_structure_invalid(self, importer: CSVImporter, temp_output_dir):
        """Test CSV structure validation with invalid file."""
        import pandas as pd
        
        invalid_csv = temp_output_dir / "invalid_structure.csv"
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['json_id', 'category'])  # Missing columns
            writer.writerow(['1', 'math'])
        
        df = pd.read_csv(invalid_csv)
        is_valid, errors = importer._validate_csv_structure(df)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required column" in error for error in errors)

    def test_validate_row_data_valid(self, importer: CSVImporter, sample_questions):
        """Test row data validation with valid data."""
        is_valid, errors = importer._validate_row_data(sample_questions[0])
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_row_data_invalid(self, importer: CSVImporter):
        """Test row data validation with invalid data."""
        invalid_row = {
            'json_id': '',  # Empty
            'category': 'math',
            'question': 'What is 2+2?',
            'golden_answer': '4',
            'answer_schema': '{"type": "object"}',
        }
        
        is_valid, errors = importer._validate_row_data(invalid_row)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("json_id" in error for error in errors)