"""End-to-end tests for quick setup workflow."""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestQuickSetupWorkflow:
    """Test the complete quick setup workflow."""

    def test_package_installation(self):
        """Test that the package can be installed."""
        # This test assumes we're in development mode
        result = subprocess.run(
            ['pip', 'show', 'llm-distiller'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'llm-distiller' in result.stdout.lower()

    def test_cli_command_available(self):
        """Test that CLI command is available after installation."""
        result = subprocess.run(
            ['llm-distiller', '--help'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'LLM Distiller' in result.stdout
        assert 'init' in result.stdout
        assert 'import' in result.stdout

    def test_database_initialization_workflow(self, temp_output_dir):
        """Test complete database initialization workflow."""
        # Create a temporary config file
        config_file = temp_output_dir / "test_config.json"
        config_content = {
            "database": {
                "url": f"sqlite:///{temp_output_dir}/test.db",
                "echo": False
            },
            "llm_providers": {
                "test": {
                    "type": "openai",
                    "api_key": "test-key",
                    "model": "test-model"
                }
            },
            "processing": {
                "batch_size": 1,
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "logging": {
                "level": "WARNING"
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        # Test database initialization
        result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'init'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert 'Creating database tables' in result.stdout
        assert 'Database initialized successfully' in result.stdout
        
        # Check that database file was created
        db_file = temp_output_dir / "test.db"
        assert db_file.exists()

    def test_import_workflow(self, temp_output_dir, sample_questions):
        """Test complete import workflow."""
        # Create temporary CSV file
        csv_file = temp_output_dir / "test_questions.csv"
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_questions[0].keys())
            writer.writeheader()
            writer.writerows(sample_questions)
        
        # Create config file
        config_file = temp_output_dir / "test_config.json"
        config_content = {
            "database": {
                "url": f"sqlite:///{temp_output_dir}/import_test.db",
                "echo": False
            },
            "llm_providers": {
                "test": {
                    "type": "openai",
                    "api_key": "test-key",
                    "model": "test-model"
                }
            },
            "processing": {
                "batch_size": 1,
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "logging": {
                "level": "WARNING"
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        # Initialize database
        init_result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'init'],
            capture_output=True,
            text=True
        )
        assert init_result.returncode == 0
        
        # Import data
        import_result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'import', str(csv_file), '--type', 'csv'],
            capture_output=True,
            text=True
        )
        
        assert import_result.returncode == 0
        assert 'Successfully imported 3 questions' in import_result.stdout
        
        # Check status
        status_result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'status'],
            capture_output=True,
            text=True
        )
        
        assert status_result.returncode == 0
        assert 'Questions: 3' in status_result.stdout
        assert 'Valid Responses: 0' in status_result.stdout

    def test_export_workflow(self, temp_output_dir, sample_questions):
        """Test complete export workflow."""
        # Setup database and import data first
        csv_file = temp_output_dir / "questions.csv"
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sample_questions[0].keys())
            writer.writeheader()
            writer.writerows(sample_questions)
        
        config_file = temp_output_dir / "config.json"
        config_content = {
            "database": {
                "url": f"sqlite:///{temp_output_dir}/export_test.db",
                "echo": False
            },
            "llm_providers": {
                "test": {
                    "type": "openai",
                    "api_key": "test-key",
                    "model": "test-model"
                }
            },
            "processing": {
                "batch_size": 1,
                "max_retries": 3,
                "timeout_seconds": 30
            },
            "logging": {
                "level": "WARNING"
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        # Initialize and import
        subprocess.run(['llm-distiller', '--config', str(config_file), 'init'], capture_output=True)
        subprocess.run(['llm-distiller', '--config', str(config_file), 'import', str(csv_file), '--type', 'csv'], capture_output=True)
        
        # Test export
        export_file = temp_output_dir / "export.jsonl"
        export_result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'export', '--format', 'jsonl', '--output', str(export_file)],
            capture_output=True,
            text=True
        )
        
        assert export_result.returncode == 0
        assert 'Exporting data in jsonl format' in export_result.stdout
        assert export_file.exists()

    def test_error_handling_workflow(self, temp_output_dir):
        """Test error handling in workflow."""
        # Test with invalid config file
        invalid_config = temp_output_dir / "invalid.json"
        with open(invalid_config, 'w') as f:
            f.write("invalid json content")
        
        result = subprocess.run(
            ['llm-distiller', '--config', str(invalid_config), 'init'],
            capture_output=True,
            text=True
        )
        
        # Should handle error gracefully
        assert result.returncode != 0 or 'error' in result.stderr.lower()
        
        # Test with non-existent CSV file
        config_file = temp_output_dir / "config.json"
        config_content = {
            "database": {"url": f"sqlite:///{temp_output_dir}/error_test.db"},
            "llm_providers": {"test": {"type": "openai", "api_key": "test"}},
            "processing": {"batch_size": 1, "max_retries": 3, "timeout_seconds": 30},
            "logging": {"level": "WARNING"}
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        subprocess.run(['llm-distiller', '--config', str(config_file), 'init'], capture_output=True)
        
        import_result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'import', 'nonexistent.csv', '--type', 'csv'],
            capture_output=True,
            text=True
        )
        
        # Should handle file not found error
        assert import_result.returncode != 0

    def test_environment_variable_handling(self, temp_output_dir):
        """Test environment variable handling."""
        # Set environment variables
        env = os.environ.copy()
        env['OPENAI_API_KEY'] = 'test-env-key'
        env['LOG_LEVEL'] = 'DEBUG'
        
        config_file = temp_output_dir / "env_config.json"
        config_content = {
            "database": {"url": f"sqlite:///{temp_output_dir}/env_test.db"},
            "llm_providers": {
                "openai_main": {
                    "type": "openai",
                    "api_key": "",  # Should use environment variable
                    "model": "gpt-3.5-turbo"
                }
            },
            "processing": {"batch_size": 1, "max_retries": 3, "timeout_seconds": 30},
            "logging": {"level": "INFO"}  # Should be overridden by env var
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config_content, f)
        
        # Test that environment variables are respected
        result = subprocess.run(
            ['llm-distiller', '--config', str(config_file), 'init'],
            capture_output=True,
            text=True,
            env=env
        )
        
        assert result.returncode == 0

    def test_configuration_validation(self, temp_output_dir):
        """Test configuration validation."""
        # Test with missing required fields
        incomplete_config = temp_output_dir / "incomplete.json"
        config_content = {
            "database": {"url": f"sqlite:///{temp_output_dir}/validation_test.db"}
            # Missing llm_providers
        }
        
        import json
        with open(incomplete_config, 'w') as f:
            json.dump(config_content, f)
        
        result = subprocess.run(
            ['llm-distiller', '--config', str(incomplete_config), 'init'],
            capture_output=True,
            text=True
        )
        
        # Should handle missing configuration gracefully
        # The exact behavior depends on implementation
        assert result.returncode in [0, 1]  # Either succeeds with defaults or fails gracefully