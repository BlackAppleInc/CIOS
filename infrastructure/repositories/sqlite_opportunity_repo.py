import sqlite3
import json
from typing import Optional, List
from datetime import datetime
from domain.opportunity import OpportunityCase, OpportunityStatus, IOpportunityRepository

class SqliteOpportunityRepository(IOpportunityRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, opportunity: OpportunityCase) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM opportunity_cases WHERE id = ?", (opportunity.id,))
            exists = cursor.fetchone() is not None
            
            raw_data_json = json.dumps(opportunity.raw_ingestion_data) if opportunity.raw_ingestion_data else None
            
            if exists:
                cursor.execute("""
                    UPDATE opportunity_cases 
                    SET title = ?, company = ?, status = ?, confidence_score = ?, 
                        raw_ingestion_data = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    opportunity.title,
                    opportunity.company,
                    opportunity.status.value,
                    opportunity.confidence_score,
                    raw_data_json,
                    opportunity.updated_at.isoformat(),
                    opportunity.id
                ))
            else:
                cursor.execute("""
                    INSERT INTO opportunity_cases 
                    (id, title, company, status, confidence_score, raw_ingestion_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity.id,
                    opportunity.title,
                    opportunity.company,
                    opportunity.status.value,
                    opportunity.confidence_score,
                    raw_data_json,
                    opportunity.created_at.isoformat(),
                    opportunity.updated_at.isoformat()
                ))
            conn.commit()

    def _map_to_domain(self, row: sqlite3.Row) -> OpportunityCase:
        return OpportunityCase(
            id=row['id'],
            title=row['title'],
            company=row['company'],
            status=OpportunityStatus(row['status']),
            confidence_score=row['confidence_score'],
            raw_ingestion_data=json.loads(row['raw_ingestion_data']) if row['raw_ingestion_data'] else None,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def find_by_id(self, id: str) -> Optional[OpportunityCase]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunity_cases WHERE id = ?", (id,))
            row = cursor.fetchone()
            return self._map_to_domain(row) if row else None

    def find_all(self) -> List[OpportunityCase]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunity_cases")
            return [self._map_to_domain(row) for row in cursor.fetchall()]

    def find_by_status(self, status: OpportunityStatus) -> List[OpportunityCase]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunity_cases WHERE status = ?", (status.value,))
            return [self._map_to_domain(row) for row in cursor.fetchall()]
