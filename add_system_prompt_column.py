#!/usr/bin/env python3
"""Database migration script to add system_prompt column to questions table."""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: str = "llm_distiller.db") -> bool:
    """Add system_prompt column to questions table.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'system_prompt' in columns:
            print("system_prompt column already exists in questions table")
            conn.close()
            return True
        
        # Add system_prompt column
        print("Adding system_prompt column to questions table...")
        cursor.execute("""
            ALTER TABLE questions 
            ADD COLUMN system_prompt TEXT
        """)
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully")
        
        # Verify column was added
        cursor.execute("PRAGMA table_info(questions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'system_prompt' in columns:
            print("✓ system_prompt column successfully added")
        else:
            print("✗ Failed to add system_prompt column")
            return False
            
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def main():
    """Main migration function."""
    # Default database path
    db_path = "llm_distiller.db"
    
    # Allow custom database path via command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database file exists
    if not Path(db_path).exists():
        print(f"Database file not found: {db_path}")
        sys.exit(1)
    
    print(f"Migrating database: {db_path}")
    
    if migrate_database(db_path):
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()