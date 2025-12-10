#!/usr/bin/env python3
"""
Migration script to add thinking columns to responses and invalid_responses tables.
"""

import sqlite3
import sys
from pathlib import Path

def add_thinking_columns():
    """Add thinking columns to database tables."""
    db_path = Path(__file__).parent / "llm_distiller.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if thinking column already exists in responses table
        cursor.execute("PRAGMA table_info(responses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'thinking' not in columns:
            print("Adding thinking column to responses table...")
            cursor.execute("ALTER TABLE responses ADD COLUMN thinking TEXT")
            print("✓ Added thinking column to responses table")
        else:
            print("✓ Thinking column already exists in responses table")
        
        # Check if thinking column already exists in invalid_responses table
        cursor.execute("PRAGMA table_info(invalid_responses)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'thinking' not in columns:
            print("Adding thinking column to invalid_responses table...")
            cursor.execute("ALTER TABLE invalid_responses ADD COLUMN thinking TEXT")
            print("✓ Added thinking column to invalid_responses table")
        else:
            print("✓ Thinking column already exists in invalid_responses table")
        
        conn.commit()
        conn.close()
        
        print("✓ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = add_thinking_columns()
    sys.exit(0 if success else 1)