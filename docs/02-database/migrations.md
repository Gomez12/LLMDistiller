# Database Migrations

Dit document beschrijft de migration strategie voor de LLM Distiller database, inclusief Alembic setup, migration best practices en version control.

## 📋 Overzicht

De migration strategie is gebaseerd op:
- **Alembic**: SQLAlchemy's migration tool
- **Version control**: Semantic versioning voor schema changes
- **Backward compatibility**: Minimal disruption voor bestaande data
- **Automated testing**: Migration testing in CI/CD

## 🏗️ Alembic Setup

### Initialisatie
```bash
# Install Alembic
pip install alembic

# Initialize Alembic in project
alembic init alembic

# Configure alembic.ini for your database
# Edit alembic/env.py to include your models
```

### Project Structuur
```
alembic/
├── versions/              # Migration files
├── env.py                 # Alembic environment configuration
├── script.py.mako         # Migration file template
├── README
└── alembic.ini            # Alembic configuration
```

### Environment Configuration
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import your models
from src.database.models import Base
from src.config.settings import Settings

# Alembic Config object
config = context.config

# Interpret config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def get_database_url():
    """Get database URL from settings"""
    try:
        settings = Settings()
        return settings.database.url
    except Exception:
        # Fallback to environment variable or default
        return os.getenv("DATABASE_URL", "sqlite:///llm_distiller.db")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## 📝 Migration Files

### Migration Template
```python
# alembic/script.py.mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

### Initial Migration (001_initial_schema.py)
```python
"""Create initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('json_id', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('golden_answer', sa.Text(), nullable=True),
        sa.Column('answer_schema', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('json_id', name='unique_json_id')
    )
    
    # Create indexes for questions
    op.create_index('idx_questions_category', 'questions', ['category'])
    op.create_index('idx_questions_json_id', 'questions', ['json_id'])
    op.create_index('idx_questions_created_at', 'questions', ['created_at'])
    
    # Create responses table
    op.create_table('responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_config', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for responses
    op.create_index('idx_responses_question_id', 'responses', ['question_id'])
    op.create_index('idx_responses_model_name', 'responses', ['model_name'])
    op.create_index('idx_responses_is_correct', 'responses', ['is_correct'])
    op.create_index('idx_responses_created_at', 'responses', ['created_at'])
    op.create_index('idx_responses_question_model', 'responses', ['question_id', 'model_name'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('responses')
    op.drop_table('questions')
```

### Adding Invalid Responses (002_add_invalid_responses.py)
```python
"""Add invalid_responses table

Revision ID: 002_add_invalid_responses
Revises: 001_initial_schema
Create Date: 2024-01-01 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_invalid_responses'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create invalid_responses table
    op.create_table('invalid_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_config', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('validation_error', sa.Text(), nullable=False),
        sa.Column('error_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for invalid_responses
    op.create_index('idx_invalid_responses_question_id', 'invalid_responses', ['question_id'])
    op.create_index('idx_invalid_responses_error_type', 'invalid_responses', ['error_type'])
    op.create_index('idx_invalid_responses_created_at', 'invalid_responses', ['created_at'])
    
    # Add check constraint for error_type
    op.create_check_constraint(
        'check_error_type',
        'invalid_responses',
        "error_type IN ('JSON_PARSE_ERROR', 'SCHEMA_VALIDATION_ERROR', 'MISSING_REQUIRED_FIELD', 'INVALID_DATA_TYPE', 'CONSTRAINT_VIOLATION')"
    )


def downgrade() -> None:
    op.drop_table('invalid_responses')
```

## 🔄 Migration Commands

### Basis Commands
```bash
# Generate new migration (autogenerate)
alembic revision --autogenerate -m "Add new feature"

# Generate empty migration
alembic revision -m "Custom migration"

# Run migrations
alembic upgrade head

# Run specific migration
alembic upgrade 002_add_invalid_responses

# Rollback migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001_initial_schema

# Show current version
alembic current

# Show migration history
alembic history

# Show upcoming migrations
alembic heads
```

### Development Workflow
```bash
# 1. Make model changes in src/database/models.py

# 2. Generate migration
alembic revision --autogenerate -m "Add new field to questions"

# 3. Review generated migration file
# Edit if necessary

# 4. Test migration on development database
alembic upgrade head

# 5. Test rollback
alembic downgrade -1
alembic upgrade head

# 6. Commit migration file to version control
git add alembic/versions/new_migration.py
git commit -m "Add migration for new field"
```

## 🧪 Testing Migrations

### Migration Testing Strategy
```python
# tests/test_migrations.py
import pytest
import tempfile
import os
from alembic.command import upgrade, downgrade
from alembic.config import Config
from sqlalchemy import create_engine, text
from src.database.models import Base

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    db_fd, db_path = tempfile.mkstemp()
    try:
        yield f"sqlite:///{db_path}"
    finally:
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def alembic_config(temp_db):
    """Create Alembic config for testing"""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", temp_db)
    return alembic_cfg

def test_upgrade_downgrade(alembic_config, temp_db):
    """Test full upgrade and downgrade cycle"""
    # Upgrade to latest
    upgrade(alembic_config, "head")
    
    # Verify tables exist
    engine = create_engine(temp_db)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        assert 'questions' in tables
        assert 'responses' in tables
        assert 'invalid_responses' in tables
    
    # Downgrade all the way
    downgrade(alembic_config, "base")
    
    # Verify tables are gone
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        assert 'questions' not in tables

def test_data_migration(alembic_config, temp_db):
    """Test migration with existing data"""
    engine = create_engine(temp_db)
    
    # Create initial schema and insert data
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO questions (category, question_text, created_at, updated_at)
            VALUES ('test', 'What is 2+2?', datetime('now'), datetime('now'))
        """))
    
    # Run migrations
    upgrade(alembic_config, "head")
    
    # Verify data is intact
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM questions"))
        count = result.scalar()
        assert count == 1
```

### CI/CD Integration
```yaml
# .github/workflows/test-migrations.yml
name: Test Database Migrations

on: [push, pull_request]

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Test SQLite migrations
      run: |
        python -m pytest tests/test_migrations.py -v
    
    - name: Test PostgreSQL migrations
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
      run: |
        alembic upgrade head
        alembic downgrade -1
        alembic upgrade head
```

## 📊 Migration Best Practices

### Do's and Don'ts

#### ✅ Do's
- **Test migrations** met real data
- **Use descriptive messages** voor migration files
- **Review auto-generated migrations** voordat je ze commit
- **Keep migrations reversible** waar mogelijk
- **Use transactions** voor data consistency
- **Document breaking changes** in migration comments

#### ❌ Don'ts
- **Don't modify existing migrations** die al in production zijn
- **Don't use `--autogenerate`** zonder review
- **Don't ignore data migration** requirements
- **Don't forget indexes** en constraints
- **Don't skip testing** rollback procedures

### Migration Patterns

#### Adding New Fields
```python
def upgrade() -> None:
    # Add nullable field first
    op.add_column('questions', sa.Column('new_field', sa.Text(), nullable=True))
    
    # Populate field with default values if needed
    op.execute("UPDATE questions SET new_field = 'default_value'")
    
    # Then make it non-nullable
    op.alter_column('questions', 'new_field', nullable=False)

def downgrade() -> None:
    op.drop_column('questions', 'new_field')
```

#### Data Type Changes
```python
def upgrade() -> None:
    # Add new column with new type
    op.add_column('questions', sa.Column('category_new', sa.String(length=200), nullable=True))
    
    # Migrate data
    op.execute("UPDATE questions SET category_new = category")
    
    # Drop old column and rename new one
    op.drop_column('questions', 'category')
    op.alter_column('questions', 'category_new', new_column_name='category')

def downgrade() -> None:
    # Reverse process
    op.add_column('questions', sa.Column('category_old', sa.String(length=100), nullable=True))
    op.execute("UPDATE questions SET category_old = category")
    op.drop_column('questions', 'category')
    op.alter_column('questions', 'category_old', new_column_name='category')
```

#### Complex Data Migration
```python
def upgrade() -> None:
    # Create new table
    op.create_table('new_table',
        # ... column definitions
    )
    
    # Migrate data in batches for large tables
    connection = op.get_bind()
    batch_size = 1000
    offset = 0
    
    while True:
        result = connection.execute(
            text("SELECT * FROM old_table LIMIT :limit OFFSET :offset"),
            {"limit": batch_size, "offset": offset}
        )
        rows = result.fetchall()
        
        if not rows:
            break
            
        # Process and insert batch
        for row in rows:
            # Transform data as needed
            connection.execute(
                text("INSERT INTO new_table (...) VALUES (...)"),
                # transformed data
            )
        
        offset += batch_size

def downgrade() -> None:
    op.drop_table('new_table')
    # Recreate old table if needed
```

## 🚀 Production Deployment

### Deployment Strategy
```bash
# 1. Backup current database
sqlite3 llm_distiller.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# 2. Run migrations in maintenance window
alembic upgrade head

# 3. Verify application functionality
python -m src.main --check

# 4. Monitor for issues
tail -f logs/llm_distiller.log
```

### Rollback Procedure
```bash
# 1. Stop application
pkill -f llm-distiller

# 2. Rollback migrations
alembic downgrade previous_version

# 3. Restore database if needed
cp backup_YYYYMMDD_HHMMSS.db llm_distiller.db

# 4. Restart application
llm-distiller serve
```

---

*Deze migration strategie zorgt voor veilige, voorspelbare database schema changes met minimale downtime en maximale data integriteit.*