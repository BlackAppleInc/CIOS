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

    _migrate_opportunity_structured_fields(db_path)

def _migrate_opportunity_structured_fields(db_path: str) -> None:
    """
    Idempotently adds the 5 structured fields to opportunity_cases.
    SQLite does not support ADD COLUMN IF NOT EXISTS, so we check
    PRAGMA table_info first and only add the column if it is absent.
    Safe to run against any existing DB (zero data loss).
    """
    NEW_COLUMNS = [
        ("location",            "TEXT"),
        ("salary_min",          "REAL"),
        ("salary_max",          "REAL"),
        ("expires_at",          "DATE"),
        ("experience_required", "TEXT"),
        ("source_platform",     "VARCHAR"),
    ]
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(opportunity_cases)")
        existing = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing:
                try:
                    conn.execute(
                        f"ALTER TABLE opportunity_cases ADD COLUMN {col_name} {col_type}"
                    )
                except Exception:
                    pass  # Already exists in a concurrent scenario; harmless
        conn.commit()

