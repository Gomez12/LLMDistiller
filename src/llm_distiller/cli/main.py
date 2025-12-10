"""CLI interface for LLM Distiller."""

import asyncio
import json
import os
from typing import Optional

import click

from ..config import Settings
from ..database import DatabaseManager, Question, Response, InvalidResponse
from ..exporters import DatasetExporter
from ..importers import CSVImporter
from ..llm import OpenAIProvider
from ..validators.schema_validator import SchemaValidator


@click.group()
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Configuration file path"
)
@click.pass_context
def cli(ctx, config: Optional[str]):
    """LLM Distiller - Create high-quality datasets for fine-tuning."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = Settings.load(config)
    ctx.obj["db_manager"] = DatabaseManager(
        database_url=ctx.obj["settings"].database.url,
        echo=ctx.obj["settings"].database.echo,
    )


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the database."""
    db_manager = ctx.obj["db_manager"]
    click.echo("Creating database tables...")
    db_manager.create_tables()
    click.echo("Database initialized successfully!")


@cli.command(name="import")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--type", "-t", type=click.Choice(["csv"]), default="csv", help="File type"
)
@click.pass_context
def import_data(ctx, file_path: str, type: str):
    """Import data from a file."""
    db_manager = ctx.obj["db_manager"]

    if type == "csv":
        importer = CSVImporter(db_manager)
    else:
        click.echo(f"Unsupported file type: {type}")
        return

    click.echo(f"Importing data from {file_path}...")

    async def run_import():
        result = await importer.import_data(file_path)
        return result

    result = asyncio.run(run_import())

    if result.success:
        click.echo(f"✅ Successfully imported {result.imported_count} questions")
    else:
        click.echo(f"❌ Import failed with {result.error_count} errors")
        for error in result.errors[:5]:  # Show first 5 errors
            click.echo(f"   • {error}")
        if len(result.errors) > 5:
            click.echo(f"   ... and {len(result.errors) - 5} more errors")


@cli.command()
@click.option("--category", "-c", help="Filter by category")
@click.option(
    "--limit", "-l", type=int, default=10, help="Number of questions to process"
)
@click.option("--provider", "-p", help="LLM provider to use")
@click.pass_context
def process(ctx, category: Optional[str], limit: int, provider: Optional[str]):
    """Process questions with LLM."""
    settings = ctx.obj["settings"]
    db_manager = ctx.obj["db_manager"]
    
    # Determine provider
    provider_name = provider or next(iter(settings.llm_providers.keys()), None)
    if not provider_name:
        click.echo("❌ No LLM provider configured. Please check your configuration.")
        return
        
    provider_config = settings.get_provider_config(provider_name)
    if not provider_config:
        click.echo(f"❌ Provider '{provider_name}' not found in configuration.")
        return

    click.echo(f"Processing up to {limit} questions with {provider_name}...")
    if category:
        click.echo(f"Filtering by category: {category}")

    # Initialize components
    try:
        llm_provider = OpenAIProvider(provider_config)
    except Exception as e:
        click.echo(f"❌ Failed to initialize provider: {e}")
        return
        
    validator = SchemaValidator()
    
    async def run_processing():
        processed_count = 0
        error_count = 0
        
        # Use a new session for processing
        with db_manager.session_scope() as session:
            # Query questions
            query = session.query(Question)
            
            if category:
                query = query.filter(Question.category == category)
                
            # Filter out questions that already have a valid response from this provider
            # This is a bit complex in SQLAlchemy without subqueries, so we'll do naive fetching for now
            # and check existence in the loop or assume we want to re-process if explicitly asked?
            # For this implementation, let's just fetch all candidates and check locally or trust the user.
            # Ideally: Left join Response where provider_name matches and is_correct is not False
            
            # Simple approach: fetch questions without responses first
            # We want to process questions that have NO response from THIS provider
            
            # Subquery for questions already processed by this provider
            processed_subquery = session.query(Response.question_id).filter(
                Response.provider_name == provider_name
            )
            
            query = query.filter(Question.id.notin_(processed_subquery))
            
            questions = query.limit(limit).all()
            
            if not questions:
                click.echo("No pending questions found to process.")
                return 0, 0

            click.echo(f"Found {len(questions)} questions to process.")
            
            for question in questions:
                try:
                    # Generate response
                    click.echo(f"Processing question {question.id}...")
                    
                    response_obj = await llm_provider.generate_response(
                        question.question_text, 
                        settings.processing.generation_params
                    )
                    
                    # Validate if schema exists
                    is_valid = True
                    error_msg = None
                    
                    if settings.processing.validate_responses and question.answer_schema:
                        try:
                            schema = json.loads(question.answer_schema)
                            validation_result = validator.validate_response(
                                response_obj.content, schema
                            )
                            is_valid = validation_result.is_valid
                            if not is_valid:
                                error_msg = "; ".join(validation_result.errors)
                        except json.JSONDecodeError:
                            # Schema itself is invalid, but we got a response
                            click.echo(f"Warning: Invalid schema for question {question.id}")
                    
                    if is_valid:
                        # Save valid response
                        new_response = Response(
                            question_id=question.id,
                            provider_name=provider_name,
                            model_name=response_obj.model,
                            response_text=response_obj.content,
                            is_correct=True, # Auto-validated by schema
                            tokens_used=response_obj.tokens_used,
                            processing_time_ms=response_obj.metadata.get("processing_time_ms")
                        )
                        session.add(new_response)
                        processed_count += 1
                        click.echo(f"✅ Question {question.id} processed successfully")
                    else:
                        # Save invalid response
                        invalid_resp = InvalidResponse(
                            question_id=question.id,
                            provider_name=provider_name,
                            model_name=response_obj.model,
                            response_text=response_obj.content,
                            error_message=error_msg or "Validation failed",
                            error_type="schema_validation",
                            tokens_used=response_obj.tokens_used,
                            processing_time_ms=response_obj.metadata.get("processing_time_ms")
                        )
                        session.add(invalid_resp)
                        error_count += 1
                        click.echo(f"⚠️ Question {question.id} validation failed: {error_msg}")
                        
                    # Commit per question to save progress? 
                    # session_scope commits at end, but we might want to commit intermediate results
                    # calling session.commit() here is safe within session_scope (it just commits transaction)
                    session.commit()
                    
                except Exception as e:
                    click.echo(f"❌ Error processing question {question.id}: {e}")
                    error_count += 1
                    # Try to save system error invalid response
                    try:
                        err_resp = InvalidResponse(
                            question_id=question.id,
                            provider_name=provider_name,
                            model_name=provider_config.model,
                            response_text="",
                            error_message=str(e),
                            error_type="system_error"
                        )
                        session.add(err_resp)
                        session.commit()
                    except:
                        session.rollback()
        
        return processed_count, error_count

    # Run logic
    processed, errors = asyncio.run(run_processing())
    
    click.echo(f"\nProcessing complete!")
    click.echo(f"✅ Successful: {processed}")
    click.echo(f"❌ Failed: {errors}")


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["jsonl", "csv", "json"]),
    default="jsonl",
    help="Export format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--validated-only", is_flag=True, help="Export only validated responses")
@click.pass_context
def export(ctx, format: str, output: Optional[str], validated_only: bool):
    """Export processed data."""
    db_manager = ctx.obj["db_manager"]

    if not output:
        output = f"export.{format}"

    click.echo(f"Exporting data in {format} format to {output}...")
    if validated_only:
        click.echo("Exporting only validated responses")

    exporter = DatasetExporter(db_manager)

    count = 0
    try:
        if format == "jsonl":
            count = exporter.export_jsonl(output, validated_only)
        elif format == "csv":
            count = exporter.export_csv(output, validated_only)
        elif format == "json":
            count = exporter.export_json(output, validated_only)

        click.echo(f"✅ Successfully exported {count} records to {output}")

    except Exception as e:
        click.echo(f"❌ Export failed: {str(e)}")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status."""
    db_manager = ctx.obj["db_manager"]

    with db_manager.session_scope() as session:
        # Imports are now top-level

        question_count = session.query(Question).count()
        response_count = session.query(Response).count()
        invalid_response_count = session.query(InvalidResponse).count()

        click.echo("📊 System Status")
        click.echo(f"Questions: {question_count}")
        click.echo(f"Valid Responses: {response_count}")
        click.echo(f"Invalid Responses: {invalid_response_count}")

        if response_count > 0:
            validated_count = (
                session.query(Response).filter(Response.is_correct == True).count()
            )
            validation_rate = (validated_count / response_count) * 100
            click.echo(f"Validation Rate: {validation_rate:.1f}%")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
