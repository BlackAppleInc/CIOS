import os
import sqlite3

def run_idempotent_initialization(db_path: str, schema_path: str = "infrastructure/database/schema.sql"):
    """
    Executes the schema file in an idempotent manner using SQLite's 
    IF NOT EXISTS clauses. Safe to run multiple times without data loss.
    """
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_script = f.read()
            conn.executescript(schema_script)
