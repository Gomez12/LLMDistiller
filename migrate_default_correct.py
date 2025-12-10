"""Database migration script to add default_correct column to questions table."""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str = "llm_distiller.db"):
    """Add default_correct column to questions table.
    
    Args:
        db_path: Path to SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'default_correct' not in columns:
            print("Adding default_correct column to questions table...")
            cursor.execute("""
                ALTER TABLE questions 
                ADD COLUMN default_correct BOOLEAN NULLABLE
            """)
            print("✅ Column added successfully")
        else:
            print("ℹ️ default_correct column already exists")
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Try common database locations
    db_paths = [
        "llm_distiller.db",
        "data/llm_distiller.db", 
        str(Path.home() / ".llm_distiller" / "llm_distiller.db")
    ]
    
    db_path = None
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break
    
    if not db_path:
        print("❌ No database found. Please specify database path:")
        print("python migrate_default_correct.py <database_path>")
        sys.exit(1)
    
    print(f"Migrating database: {db_path}")
    migrate_database(db_path)
    print("🎉 Migration completed!")