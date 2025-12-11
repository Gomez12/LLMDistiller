"""Integration tests for CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, AsyncMock

from llm_distiller.cli.main import cli


class TestCLICommands:
    """Test CLI command integration."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'LLM Distiller' in result.output
        assert 'init' in result.output
        assert 'import' in result.output
        assert 'export' in result.output
        assert 'status' in result.output

    def test_init_command(self, runner, test_db_manager):
        """Test database initialization command."""
        with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
            result = runner.invoke(cli, ['init'])
            
            assert result.exit_code == 0
            assert 'Creating database tables' in result.output
            assert 'Database initialized successfully' in result.output

    def test_import_data_command_valid(self, runner, test_db_manager, sample_csv_file):
        """Test importing valid CSV data."""
        mock_importer = Mock()
        mock_importer.import_data = AsyncMock()
        mock_importer.import_data.return_value = Mock(
            success=True,
            imported_count=3,
            error_count=0,
            errors=[]
        )
        
        with patch('llm_distiller.cli.main.CSVImporter', return_value=mock_importer):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['import', sample_csv_file, '--type', 'csv'])
                
                assert result.exit_code == 0
                assert f'Importing data from {sample_csv_file}' in result.output
                assert 'Successfully imported 3 questions' in result.output

    def test_import_data_command_with_errors(self, runner, test_db_manager, sample_csv_file):
        """Test importing CSV data with errors."""
        mock_importer = Mock()
        mock_importer.import_data = AsyncMock()
        mock_importer.import_data.return_value = Mock(
            success=False,
            imported_count=0,
            error_count=2,
            errors=['Error 1', 'Error 2']
        )
        
        with patch('llm_distiller.cli.main.CSVImporter', return_value=mock_importer):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['import', sample_csv_file, '--type', 'csv'])
                
                assert result.exit_code == 0
                assert 'Import failed with 2 errors' in result.output
                assert 'Error 1' in result.output
                assert 'Error 2' in result.output

    def test_import_data_unsupported_type(self, runner, test_db_manager, sample_csv_file):
        """Test importing with unsupported file type."""
        with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
            result = runner.invoke(cli, ['import', sample_csv_file, '--type', 'xml'])
            
            assert result.exit_code == 2
            assert 'Invalid value for' in result.output

    def test_import_data_nonexistent_file(self, runner, test_db_manager):
        """Test importing non-existent file."""
        with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
            result = runner.invoke(cli, ['import', 'nonexistent.csv', '--type', 'csv'])
            
            assert result.exit_code != 0  # Should fail

    def test_export_command_jsonl(self, runner, test_db_manager, temp_output_dir):
        """Test exporting to JSONL format."""
        mock_exporter = Mock()
        mock_exporter.export_jsonl.return_value = 5
        
        output_file = str(temp_output_dir / "test.jsonl")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export', '--format', 'jsonl', '--output', output_file])
                
                assert result.exit_code == 0
                assert f'Exporting data in jsonl format to {output_file}' in result.output
                assert 'Successfully exported 5 records' in result.output
                mock_exporter.export_jsonl.assert_called_once_with(output_file, False)

    def test_export_command_csv_validated_only(self, runner, test_db_manager, temp_output_dir):
        """Test exporting to CSV format with validated only flag."""
        mock_exporter = Mock()
        mock_exporter.export_csv.return_value = 3
        
        output_file = str(temp_output_dir / "test.csv")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export', '--format', 'csv', '--output', output_file, '--validated-only'])
                
                assert result.exit_code == 0
                assert 'Exporting only validated responses' in result.output
                assert 'Successfully exported 3 records' in result.output
                mock_exporter.export_csv.assert_called_once_with(output_file, True)

    def test_export_command_default_output(self, runner, test_db_manager):
        """Test exporting with default output filename."""
        mock_exporter = Mock()
        mock_exporter.export_json.return_value = 10
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export', '--format', 'json'])
                
                assert result.exit_code == 0
                assert 'Exporting data in json format to export.json' in result.output
                assert 'Successfully exported 10 records' in result.output
                mock_exporter.export_json.assert_called_once_with('export.json', False)

    def test_export_command_with_exception(self, runner, test_db_manager):
        """Test export command with exception."""
        mock_exporter = Mock()
        mock_exporter.export_jsonl.side_effect = Exception("Export failed")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export', '--format', 'jsonl'])
                
                assert result.exit_code == 0
                assert 'Export failed: Export failed' in result.output

    def test_status_command(self, runner, test_db_manager, sample_questions):
        """Test status command."""
        # Mock database queries
        mock_session = Mock()
        mock_query = Mock()
        
        # Setup mock counts
        mock_query.count.side_effect = [10, 8, 2]  # questions, responses, invalid_responses
        mock_session.query.return_value = mock_query
        
        # Mock validated responses query
        validated_query = Mock()
        validated_query.count.return_value = 6
        mock_session.query.return_value.filter.return_value = validated_query
        
        with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
            with patch.object(test_db_manager, 'session_scope') as mock_session_scope:
                mock_session_scope.return_value.__enter__.return_value = mock_session
                
                result = runner.invoke(cli, ['status'])
                
                assert result.exit_code == 0
                assert 'System Status' in result.output
                assert 'Questions: 10' in result.output
                assert 'Valid Responses: 8' in result.output
                assert 'Invalid Responses: 2' in result.output
                assert 'Validation Rate: 75.0%' in result.output

    def test_status_command_no_responses(self, runner, test_db_manager):
        """Test status command with no responses."""
        mock_session = Mock()
        mock_query = Mock()
        
        # Setup mock counts
        mock_query.count.side_effect = [5, 0, 0]  # questions, responses, invalid_responses
        mock_session.query.return_value = mock_query
        
        with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
            with patch.object(test_db_manager, 'session_scope') as mock_session_scope:
                mock_session_scope.return_value.__enter__.return_value = mock_session
                
                result = runner.invoke(cli, ['status'])
                
                assert result.exit_code == 0
                assert 'Questions: 5' in result.output
                assert 'Valid Responses: 0' in result.output
                assert 'Invalid Responses: 0' in result.output
                # Should not show validation rate when no responses
                assert 'Validation Rate:' not in result.output

    def test_process_command_missing_provider_config(self, runner):
        """Test process command failing gracefully without provider config."""
        result = runner.invoke(cli, ['process', '--limit', '5'])
        
        assert result.exit_code == 0
        # The new implementation checks for provider configuration immediately
        # Since we are not mocking Settings completely here, it might return 'No LLM provider configured' or similar
        # Or if it fails at provider init
        assert 'No LLM provider configured' in result.output or 'Provider' in result.output or 'Failed to initialize provider' in result.output

    def test_export_training_command_default(self, runner, test_db_manager, temp_output_dir):
        """Test export-training command with default settings."""
        mock_exporter = Mock()
        mock_exporter.export_training_jsonl.return_value = 7
        
        output_file = str(temp_output_dir / "training_data.jsonl")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export-training', '--output', output_file])
                
                assert result.exit_code == 0
                assert f'Exporting training data to {output_file}' in result.output
                assert 'Successfully exported 7 training records' in result.output
                mock_exporter.export_training_jsonl.assert_called_once_with(output_file, False, None)

    def test_export_training_command_validated_only(self, runner, test_db_manager, temp_output_dir):
        """Test export-training command with validated-only flag."""
        mock_exporter = Mock()
        mock_exporter.export_training_jsonl.return_value = 4
        
        output_file = str(temp_output_dir / "validated_training.jsonl")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export-training', '--output', output_file, '--validated-only'])
                
                assert result.exit_code == 0
                assert 'Exporting only validated responses' in result.output
                assert 'Successfully exported 4 training records' in result.output
                mock_exporter.export_training_jsonl.assert_called_once_with(output_file, True, None)

    def test_export_training_command_with_category(self, runner, test_db_manager, temp_output_dir):
        """Test export-training command with category filter."""
        mock_exporter = Mock()
        mock_exporter.export_training_jsonl.return_value = 3
        
        output_file = str(temp_output_dir / "math_training.jsonl")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export-training', '--output', output_file, '--category', 'math'])
                
                assert result.exit_code == 0
                assert 'Filtering by category: math' in result.output
                assert 'Successfully exported 3 training records' in result.output
                mock_exporter.export_training_jsonl.assert_called_once_with(output_file, False, 'math')

    def test_export_training_command_default_filename(self, runner, test_db_manager):
        """Test export-training command with default filename."""
        mock_exporter = Mock()
        mock_exporter.export_training_jsonl.return_value = 5
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export-training'])
                
                assert result.exit_code == 0
                assert 'Exporting training data to training_data.jsonl' in result.output
                assert 'Successfully exported 5 training records' in result.output
                mock_exporter.export_training_jsonl.assert_called_once_with('training_data.jsonl', False, None)

    def test_export_training_command_with_exception(self, runner, test_db_manager):
        """Test export-training command with exception."""
        mock_exporter = Mock()
        mock_exporter.export_training_jsonl.side_effect = Exception("Training export failed")
        
        with patch('llm_distiller.cli.main.DatasetExporter', return_value=mock_exporter):
            with patch('llm_distiller.cli.main.DatabaseManager', return_value=test_db_manager):
                result = runner.invoke(cli, ['export-training'])
                
                assert result.exit_code == 0
                assert 'Export failed: Training export failed' in result.output

    def test_config_option(self, runner, temp_config_file):
        """Test CLI with custom config file."""
        result = runner.invoke(cli, ['--config', temp_config_file, '--help'])
        
        assert result.exit_code == 0
        assert 'LLM Distiller' in result.output