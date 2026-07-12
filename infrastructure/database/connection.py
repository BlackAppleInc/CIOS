import os
import sqlite3
import threading
from typing import Generator
from contextlib import contextmanager

def resolve_db_path(explicit_path: str = None) -> str:
    if explicit_path:
        return explicit_path
    env = os.environ.get("CIOS_ENV", "production").lower()
    if env == "test":
        return "test_cios.db"
    return "data/cios.db"

class DatabaseConnectionManager:
    """Manages SQLite connections and ensures PRAGMA foreign_keys = ON."""
    
    def __init__(self, db_path: str = None):
        self.db_path = resolve_db_path(db_path)
        self._local = threading.local()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        # Using check_same_thread=False allows threading but requires care.
        # SQLite handles concurrent reads, but writes lock the DB.
        conn = sqlite3.connect(self.db_path, uri=True, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
