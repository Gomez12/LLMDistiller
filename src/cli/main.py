"""CLI interface for LLM Distiller."""

import asyncio
import logging
import os
from typing import Optional

import click

from ..config import Settings
from ..database import DatabaseManager
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
    
    # Setup logging
    logging_config = ctx.obj["settings"].logging
    
    # Set log level - use DEBUG for TRACE since we can't easily add custom levels
    log_level_str = logging_config.level.upper()
    if log_level_str == "TRACE":
        log_level = logging.DEBUG  # Use DEBUG level for TRACE
    else:
        log_level = getattr(logging, log_level_str)
    
    logging.basicConfig(
        level=log_level,
        format=logging_config.format,
        filename=logging_config.file_path
    )
    
    # Also log to console for errors and above if enabled
    if logging_config.console_errors:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logging.getLogger().addHandler(console_handler)
    
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


@cli.group(name="import")
def import_cmd():
    """Import data from various sources."""
    pass


@import_cmd.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--default-correct", help="Default correct answer for missing values")
@click.pass_context
def csv(ctx, file_path: str, default_correct: Optional[str]):
    """Import data from a CSV file."""
    db_manager = ctx.obj["db_manager"]
    importer = CSVImporter(db_manager)

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
    click.echo(f"Processing {limit} questions...")
    if category:
        click.echo(f"Filtering by category: {category}")
    if provider:
        click.echo(f"Using provider: {provider}")

    async def run_processing():
        from ..processing import ProcessingEngine
        
        engine = ProcessingEngine(
            db_manager=ctx.obj["db_manager"],
            settings=ctx.obj["settings"]
        )
        
        if provider:
            click.echo(f"Using provider: {provider}")
        else:
            available_providers = list(ctx.obj["settings"].llm_providers.keys())
            if available_providers:
                click.echo(f"No provider specified, will use load balancing across: {', '.join(available_providers)}")
            else:
                click.echo("Warning: No providers configured")
        
        result = await engine.process_questions(
            category=category,
            limit=limit,
            provider=provider
        )
        
        # Display results
        if result.success:
            click.echo(f"✅ Processing completed successfully!")
            click.echo(f"📊 Results:")
            click.echo(f"   Total questions: {result.stats.total_questions}")
            click.echo(f"   Processed: {result.stats.processed_questions}")
            click.echo(f"   Successful: {result.stats.successful_responses}")
            click.echo(f"   Failed: {result.stats.failed_responses}")
            click.echo(f"   Invalid: {result.stats.invalid_responses}")
            
            if result.stats.processing_time_seconds > 0:
                click.echo(f"   Processing time: {result.stats.processing_time_seconds:.1f}s")
                click.echo(f"   Speed: {result.stats.questions_per_second:.1f} questions/sec")
            
            if result.stats.total_tokens_used > 0:
                click.echo(f"   Total tokens: {result.stats.total_tokens_used:,}")
                click.echo(f"   Avg tokens/question: {result.stats.average_tokens_per_question:.0f}")
            
            if result.errors:
                click.echo(f"⚠️  Warnings/Errors:")
                for error in result.errors[:5]:
                    click.echo(f"   • {error}")
                if len(result.errors) > 5:
                    click.echo(f"   ... and {len(result.errors) - 5} more")
        else:
            click.echo(f"❌ Processing failed!")
            for error in result.errors:
                click.echo(f"   • {error}")

    import asyncio
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
        from ..database.models import InvalidResponse, Question, Response

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
