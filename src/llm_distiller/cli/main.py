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
        pool_size=ctx.obj["settings"].database.pool_size,
        max_overflow=ctx.obj["settings"].database.max_overflow,
        pool_pre_ping=ctx.obj["settings"].database.pool_pre_ping,
        pool_recycle=ctx.obj["settings"].database.pool_recycle,
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
@click.option(
    "--default-correct",
    type=click.Choice(["true", "false", "null"]),
    help="Default waarde voor is_correct (null/true/false)"
)
@click.pass_context
def import_data(ctx, file_path: str, type: str, default_correct: Optional[str]):
    """Import data from a file."""
    db_manager = ctx.obj["db_manager"]

    # Convert default_correct string to boolean/None
    default_correct_value = None
    if default_correct:
        if default_correct.lower() == "true":
            default_correct_value = True
        elif default_correct.lower() == "false":
            default_correct_value = False
        elif default_correct.lower() == "null":
            default_correct_value = None

    if type == "csv":
        importer = CSVImporter(db_manager, default_correct=default_correct_value)
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
@click.option(
    "--system-prompt", "-s", help="Default system prompt to use for all questions"
)
@click.pass_context
def process(ctx, category: Optional[str], limit: int, provider: Optional[str], system_prompt: Optional[str]):
    """Process questions with LLM."""
    settings = ctx.obj["settings"]
    db_manager = ctx.obj["db_manager"]
    
    # Use the processing engine
    from processing.engine import ProcessingEngine
    engine = ProcessingEngine(db_manager, settings)
    
    click.echo(f"Processing up to {limit} questions...")
    if category:
        click.echo(f"Filtering by category: {category}")
    if provider:
        click.echo(f"Using provider: {provider}")
    
    async def run_processing():
        result = await engine.process_questions(category, limit, provider, system_prompt)
        
        # Report results
        click.echo(f"\nProcessing complete!")
        click.echo(f"✅ Successful: {result.stats.successful_responses}")
        click.echo(f"❌ Failed: {result.stats.failed_responses}")
        
        if result.stats.invalid_responses > 0:
            click.echo(f"⚠️ Invalid responses: {result.stats.invalid_responses}")
        
        if result.stats.total_tokens_used > 0:
            click.echo(f"🔤 Total tokens used: {result.stats.total_tokens_used}")
        
        if result.stats.processing_time_seconds > 0:
            click.echo(f"⏱️ Processing time: {result.stats.processing_time_seconds:.2f}s")
            click.echo(f"📊 Speed: {result.stats.questions_per_second:.2f} questions/second")
        
        if result.errors:
            click.echo(f"\n❌ Errors:")
            for error in result.errors:
                click.echo(f"   • {error}")
        
        if result.warnings:
            click.echo(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                click.echo(f"   • {warning}")
    
    asyncio.run(run_processing())


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
