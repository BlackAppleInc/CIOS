import json
import uuid
from typing import Optional, List
from datetime import datetime

from domain.opportunity import OpportunityCase, OpportunityStatus, Interaction, InteractionType, ApplicationEvent, ApplicationEventType, Reminder, Document, CVVersion, Offer
from domain.contact import Contact
from domain.company import Company

from core.ports.repository import IRepository
from infrastructure.database.connection import DatabaseConnectionManager

class SqliteOpportunityRepository(IRepository[OpportunityCase]):
    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.conn_manager = connection_manager

    def _resolve_company_id(self, cursor, company_name: str) -> Optional[int]:
        if not company_name:
            return None
        cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
        row = cursor.fetchone()
        if row:
            return row[0]
        business_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO companies (business_id, name) VALUES (?, ?)", (business_id, company_name))
        return cursor.lastrowid

    def _resolve_contact_id(self, cursor, contact: Contact) -> Optional[int]:
        if not contact:
            return None
        cursor.execute("SELECT id FROM contacts WHERE business_id = ?", (contact.id,))
        row = cursor.fetchone()
        if row:
            return row[0]
        company_id = self._resolve_company_id(cursor, contact.company.name) if contact.company else None
        cursor.execute("""
            INSERT INTO contacts (business_id, first_name, last_name, email, phone, company_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (contact.id, contact.first_name, contact.last_name, contact.email, contact.phone, company_id))
        return cursor.lastrowid

    def _resolve_cv_version_id(self, cursor, cv_version: CVVersion) -> Optional[int]:
        if not cv_version: return None
        cursor.execute("SELECT id FROM cv_versions WHERE business_id = ?", (cv_version.id,))
        row = cursor.fetchone()
        if row: return row[0]
        cursor.execute("""
            INSERT INTO cv_versions (business_id, name, file_path)
            VALUES (?, ?, ?)
        """, (cv_version.id, cv_version.name, cv_version.file_path))
        return cursor.lastrowid

    def _sync_interactions(self, cursor, opp_id: int, interactions: List[Interaction]):
        if interactions:
            placeholders = ",".join("?" for _ in interactions)
            params = [opp_id] + [i.id for i in interactions]
            cursor.execute(f"DELETE FROM interactions WHERE opportunity_id = ? AND business_id NOT IN ({placeholders})", params)
        else:
            cursor.execute("DELETE FROM interactions WHERE opportunity_id = ?", (opp_id,))

        for i in interactions:
            contact_id = self._resolve_contact_id(cursor, i.contact) if i.contact else None
            cursor.execute("""
                INSERT INTO interactions (
                    business_id, contact_id, opportunity_id, interaction_type, interaction_date, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    contact_id=excluded.contact_id,
                    interaction_type=excluded.interaction_type,
                    interaction_date=excluded.interaction_date,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
            """, (
                i.id, contact_id, opp_id, i.interaction_type.value, i.interaction_date.isoformat(),
                i.notes, i.created_at.isoformat(), i.updated_at.isoformat()
            ))

    def _sync_events(self, cursor, opp_id: int, events: List[ApplicationEvent]):
        if events:
            placeholders = ",".join("?" for _ in events)
            params = [opp_id] + [e.id for e in events]
            cursor.execute(f"DELETE FROM application_events WHERE opportunity_id = ? AND business_id NOT IN ({placeholders})", params)
        else:
            cursor.execute("DELETE FROM application_events WHERE opportunity_id = ?", (opp_id,))

        for e in events:
            cv_id = self._resolve_cv_version_id(cursor, e.cv_version) if e.cv_version else None
            cursor.execute("""
                INSERT INTO application_events (
                    business_id, opportunity_id, event_type, event_date, cv_version_id, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    event_type=excluded.event_type,
                    event_date=excluded.event_date,
                    cv_version_id=excluded.cv_version_id,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
            """, (
                e.id, opp_id, e.event_type.value, e.event_date.isoformat(), cv_id, e.notes,
                e.created_at.isoformat(), e.updated_at.isoformat()
            ))

    def _sync_reminders(self, cursor, opp_id: int, reminders: List[Reminder]):
        if reminders:
            placeholders = ",".join("?" for _ in reminders)
            params = [opp_id] + [r.id for r in reminders]
            cursor.execute(f"DELETE FROM reminders WHERE opportunity_id = ? AND business_id NOT IN ({placeholders})", params)
        else:
            cursor.execute("DELETE FROM reminders WHERE opportunity_id = ?", (opp_id,))

        for r in reminders:
            cursor.execute("""
                INSERT INTO reminders (
                    business_id, opportunity_id, remind_at, description, is_completed, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    remind_at=excluded.remind_at,
                    description=excluded.description,
                    is_completed=excluded.is_completed,
                    updated_at=excluded.updated_at
            """, (
                r.id, opp_id, r.remind_at.isoformat(), r.description, 1 if r.is_completed else 0,
                r.created_at.isoformat(), r.updated_at.isoformat()
            ))

    def _sync_documents(self, cursor, opp_id: int, documents: List[Document]):
        if documents:
            placeholders = ",".join("?" for _ in documents)
            params = [opp_id] + [d.id for d in documents]
            cursor.execute(f"DELETE FROM documents WHERE opportunity_id = ? AND business_id NOT IN ({placeholders})", params)
        else:
            cursor.execute("DELETE FROM documents WHERE opportunity_id = ?", (opp_id,))

        for d in documents:
            cursor.execute("""
                INSERT INTO documents (
                    business_id, opportunity_id, name, file_path, document_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    name=excluded.name,
                    file_path=excluded.file_path,
                    document_type=excluded.document_type,
                    updated_at=excluded.updated_at
            """, (
                d.id, opp_id, d.name, d.file_path, d.document_type,
                d.created_at.isoformat(), d.updated_at.isoformat()
            ))

    def _sync_offers(self, cursor, opp_id: int, offers: List[Offer]):
        if offers:
            placeholders = ",".join("?" for _ in offers)
            params = [opp_id] + [o.id for o in offers]
            cursor.execute(f"DELETE FROM offers WHERE opportunity_id = ? AND business_id NOT IN ({placeholders})", params)
        else:
            cursor.execute("DELETE FROM offers WHERE opportunity_id = ?", (opp_id,))

        for o in offers:
            cursor.execute("""
                INSERT INTO offers (
                    business_id, opportunity_id, base_salary, bonus_percentage, equity_value, benefits_summary, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    base_salary=excluded.base_salary,
                    bonus_percentage=excluded.bonus_percentage,
                    equity_value=excluded.equity_value,
                    benefits_summary=excluded.benefits_summary,
                    updated_at=excluded.updated_at
            """, (
                o.id, opp_id, o.base_salary, o.bonus_percentage, o.equity_value, o.benefits_summary,
                o.created_at.isoformat(), o.updated_at.isoformat()
            ))

    def save(self, opportunity: OpportunityCase) -> None:
        insert_query = """
            INSERT INTO opportunity_cases (
                business_id, company_id, title, status, confidence_score, raw_ingestion_data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(business_id) DO UPDATE SET
                company_id=excluded.company_id,
                title=excluded.title,
                status=excluded.status,
                confidence_score=excluded.confidence_score,
                raw_ingestion_data=excluded.raw_ingestion_data,
                updated_at=excluded.updated_at
        """
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            company_id = self._resolve_company_id(cursor, opportunity.company)
            
            raw_data = opportunity.raw_ingestion_data
            if not isinstance(raw_data, str) and raw_data is not None:
                raw_data = json.dumps(raw_data)

            cursor.execute(insert_query, (
                opportunity.id,
                company_id,
                opportunity.title,
                opportunity.status.value,
                opportunity.confidence_score,
                raw_data,
                opportunity.created_at.isoformat(),
                opportunity.updated_at.isoformat()
            ))

            cursor.execute("SELECT id FROM opportunity_cases WHERE business_id = ?", (opportunity.id,))
            opportunity_internal_id = cursor.fetchone()[0]

            self._sync_interactions(cursor, opportunity_internal_id, opportunity.interactions)
            self._sync_events(cursor, opportunity_internal_id, opportunity.events)
            self._sync_reminders(cursor, opportunity_internal_id, opportunity.reminders)
            self._sync_documents(cursor, opportunity_internal_id, opportunity.documents)
            self._sync_offers(cursor, opportunity_internal_id, opportunity.offers)

    def update(self, opportunity: OpportunityCase) -> None:
        """Atomic transaction to update status and cascade entity graph."""
        # Our implementation of self.conn_manager.get_connection() already yields 
        # a context manager that ensures atomic transactions (commits on exit, rolls back on exception)
        # Since 'save()' uses the same ON CONFLICT DO UPDATE behavior and cascades everything properly,
        # we can delegate to it to guarantee memory graph synchronization without rewriting query logic.
        self.save(opportunity)

    def _get_interactions(self, cursor, opp_id: int) -> List[Interaction]:
        cursor.execute("""
            SELECT i.*, c.business_id as c_bus, c.first_name, c.last_name, c.email, c.phone, comp.name as comp_name, comp.business_id as comp_bus
            FROM interactions i
            LEFT JOIN contacts c ON i.contact_id = c.id
            LEFT JOIN companies comp ON c.company_id = comp.id
            WHERE i.opportunity_id = ?
        """, (opp_id,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            contact = None
            if row[2]: # contact_id is not null
                comp = None
                if row[14]:
                    comp = Company(id=row[15], name=row[14])
                contact = Contact(
                    id=row[9],
                    first_name=row[10],
                    last_name=row[11],
                    email=row[12],
                    phone=row[13],
                    company=comp
                )
            res.append(Interaction(
                id=row[1],
                interaction_type=InteractionType(row[4]),
                interaction_date=datetime.fromisoformat(row[5]),
                notes=row[6],
                contact=contact,
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            ))
        return res

    def _get_events(self, cursor, opp_id: int) -> List[ApplicationEvent]:
        cursor.execute("""
            SELECT e.*, cv.business_id as cv_bus, cv.name as cv_name, cv.file_path as cv_path
            FROM application_events e
            LEFT JOIN cv_versions cv ON e.cv_version_id = cv.id
            WHERE e.opportunity_id = ?
        """, (opp_id,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            cv = None
            if row[5]:
                cv = CVVersion(id=row[9], name=row[10], file_path=row[11])
            res.append(ApplicationEvent(
                id=row[1],
                event_type=ApplicationEventType(row[3]),
                event_date=datetime.fromisoformat(row[4]),
                notes=row[6],
                cv_version=cv,
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            ))
        return res

    def _get_reminders(self, cursor, opp_id: int) -> List[Reminder]:
        cursor.execute("SELECT * FROM reminders WHERE opportunity_id = ?", (opp_id,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append(Reminder(
                id=row[1],
                remind_at=datetime.fromisoformat(row[3]),
                description=row[4],
                is_completed=bool(row[5]),
                created_at=datetime.fromisoformat(row[6]),
                updated_at=datetime.fromisoformat(row[7])
            ))
        return res

    def _get_documents(self, cursor, opp_id: int) -> List[Document]:
        cursor.execute("SELECT * FROM documents WHERE opportunity_id = ?", (opp_id,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append(Document(
                id=row[1],
                name=row[3],
                file_path=row[4],
                document_type=row[5],
                created_at=datetime.fromisoformat(row[6]),
                updated_at=datetime.fromisoformat(row[7])
            ))
        return res

    def _get_offers(self, cursor, opp_id: int) -> List[Offer]:
        cursor.execute("SELECT * FROM offers WHERE opportunity_id = ?", (opp_id,))
        rows = cursor.fetchall()
        res = []
        for row in rows:
            res.append(Offer(
                id=row[1],
                base_salary=row[3] or 0.0,
                bonus_percentage=row[4] or 0.0,
                equity_value=row[5] or 0.0,
                benefits_summary=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            ))
        return res

    def get_by_business_id(self, business_id: str) -> Optional[OpportunityCase]:
        query = """
            SELECT oc.*, c.name as company_name 
            FROM opportunity_cases oc
            LEFT JOIN companies c ON oc.company_id = c.id
            WHERE oc.business_id = ?
        """
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (business_id,))
            row = cursor.fetchone()

            if not row:
                return None

            opp_internal_id = row[0]
            company_name = row[9] or ""

            raw_data = None
            if row[6]:
                try:
                    raw_data = json.loads(row[6])
                except (json.JSONDecodeError, TypeError):
                    raw_data = row[6]

            opp = OpportunityCase(
                id=row[1],
                title=row[3] or "",
                company=company_name,
                status=OpportunityStatus(row[4]),
                confidence_score=row[5],
                raw_ingestion_data=raw_data,
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )

            opp.interactions = self._get_interactions(cursor, opp_internal_id)
            opp.events = self._get_events(cursor, opp_internal_id)
            opp.reminders = self._get_reminders(cursor, opp_internal_id)
            opp.documents = self._get_documents(cursor, opp_internal_id)
            opp.offers = self._get_offers(cursor, opp_internal_id)

            return opp

    def delete(self, business_id: str) -> None:
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM opportunity_cases WHERE business_id = ?", (business_id,))

    def get_all(self, status: Optional[OpportunityStatus] = None) -> List[OpportunityCase]:
        query = """
            SELECT oc.*, c.name as company_name 
            FROM opportunity_cases oc
            LEFT JOIN companies c ON oc.company_id = c.id
        """
        params = []
        if status is not None:
            query += " WHERE oc.status = ?"
            params.append(status.value)

        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                opp_internal_id = row[0]
                company_name = row[9] or ""

                raw_data = None
                if row[6]:
                    try:
                        raw_data = json.loads(row[6])
                    except (json.JSONDecodeError, TypeError):
                        raw_data = row[6]

                opp = OpportunityCase(
                    id=row[1],
                    title=row[3] or "",
                    company=company_name,
                    status=OpportunityStatus(row[4]),
                    confidence_score=row[5],
                    raw_ingestion_data=raw_data,
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8])
                )

                opp.interactions = self._get_interactions(cursor, opp_internal_id)
                opp.events = self._get_events(cursor, opp_internal_id)
                opp.reminders = self._get_reminders(cursor, opp_internal_id)
                opp.documents = self._get_documents(cursor, opp_internal_id)
                opp.offers = self._get_offers(cursor, opp_internal_id)

                results.append(opp)

            return results

    def get_pending_reminders(self) -> List[tuple[Reminder, str, str]]:
        query = """
            SELECT r.*, oc.title, oc.business_id as opp_bus_id
            FROM reminders r
            JOIN opportunity_cases oc ON r.opportunity_id = oc.id
            WHERE r.is_completed = 0
            ORDER BY r.reminder_date ASC
        """
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Assuming table schema for reminders matches how we insert: 
                # id(0), opportunity_id(1), business_id(2), reminder_date(3), note(4), is_completed(5)
                # plus our selected extras: title(-2), opp_bus_id(-1)
                
                # We need to construct the Reminder
                # Since we don't know the exact column order if schema changed, let's look at _sync_reminders or _get_reminders
                # from the previous code, _get_reminders parses:
                # row[2] = business_id
                # row[3] = reminder_date
                # row[4] = note
                # row[5] = is_completed
                # row[-2] = title, row[-1] = opp_bus_id
                
                rem = Reminder(
                    id=row[2],
                    reminder_date=datetime.fromisoformat(row[3]),
                    note=row[4],
                    is_completed=bool(row[5])
                )
                title = row[-2] or ""
                opp_bus_id = row[-1]
                
                results.append((rem, title, opp_bus_id))
                
            return results

    def get_pipeline_analytics(self) -> dict:
        analytics = {
            "total_cases": 0,
            "status_distribution": {},
            "funnel": {
                "applied": 0,
                "interviewed": 0,
                "offers": 0
            },
            "conversion_rates": {
                "applied_to_interview": 0.0,
                "interview_to_offer": 0.0,
                "overall_win_rate": 0.0
            }
        }
        
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Total Cases & Status Distribution
            cursor.execute("SELECT status, COUNT(*) FROM opportunity_cases GROUP BY status")
            rows = cursor.fetchall()
            
            for row in rows:
                status, count = row
                analytics["status_distribution"][status] = count
                analytics["total_cases"] += count
                
            # 2. Funnel Metrics (Offloaded to SQLite)
            funnel_query = """
                WITH CaseSummary AS (
                    SELECT oc.id, oc.status, IFNULL(GROUP_CONCAT(ae.event_type), '') as events
                    FROM opportunity_cases oc
                    LEFT JOIN application_events ae ON oc.id = ae.opportunity_id
                    GROUP BY oc.id
                )
                SELECT 
                    SUM(CASE WHEN status IN ('Applied', 'Interview', 'Offer') 
                        OR events LIKE '%Submission%' 
                        OR events LIKE '%Interview%' 
                        OR events LIKE '%Offer%' THEN 1 ELSE 0 END) as applied,
                    SUM(CASE WHEN status IN ('Interview', 'Offer') 
                        OR events LIKE '%Interview%' 
                        OR events LIKE '%Offer%' THEN 1 ELSE 0 END) as interviewed,
                    SUM(CASE WHEN status = 'Offer' 
                        OR events LIKE '%Offer%' THEN 1 ELSE 0 END) as offers
                FROM CaseSummary;
            """
            cursor.execute(funnel_query)
            funnel_row = cursor.fetchone()
            
            if funnel_row:
                applied = funnel_row[0] or 0
                interviewed = funnel_row[1] or 0
                offers = funnel_row[2] or 0
                
                analytics["funnel"]["applied"] = applied
                analytics["funnel"]["interviewed"] = interviewed
                analytics["funnel"]["offers"] = offers
                
                if applied > 0:
                    analytics["conversion_rates"]["applied_to_interview"] = round((interviewed / applied) * 100, 1)
                    analytics["conversion_rates"]["overall_win_rate"] = round((offers / applied) * 100, 1)
                    
                if interviewed > 0:
                    analytics["conversion_rates"]["interview_to_offer"] = round((offers / interviewed) * 100, 1)
                    
        return analytics

    def search(self, keyword: str) -> List[OpportunityCase]:
        query = """
            SELECT DISTINCT oc.*, c.name as company_name 
            FROM opportunity_cases oc
            LEFT JOIN companies c ON oc.company_id = c.id
            LEFT JOIN interactions i ON oc.id = i.opportunity_id
            LEFT JOIN contacts con ON i.contact_id = con.id
            WHERE oc.title LIKE ?
               OR c.name LIKE ?
               OR i.notes LIKE ?
               OR con.first_name LIKE ?
               OR con.last_name LIKE ?
        """
        like_pattern = f"%{keyword}%"
        params = [like_pattern] * 5

        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                opp_internal_id = row[0]
                company_name = row[9] or ""

                raw_data = None
                if row[6]:
                    try:
                        raw_data = json.loads(row[6])
                    except (json.JSONDecodeError, TypeError):
                        raw_data = row[6]

                opp = OpportunityCase(
                    id=row[1],
                    title=row[3] or "",
                    company=company_name,
                    status=OpportunityStatus(row[4]),
                    confidence_score=row[5],
                    raw_ingestion_data=raw_data,
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8])
                )

                opp.interactions = self._get_interactions(cursor, opp_internal_id)
                opp.events = self._get_events(cursor, opp_internal_id)
                opp.reminders = self._get_reminders(cursor, opp_internal_id)
                opp.documents = self._get_documents(cursor, opp_internal_id)
                opp.offers = self._get_offers(cursor, opp_internal_id)

                results.append(opp)

            return results

    def get_global_network(self) -> List[dict]:
        query = """
            SELECT 
                c.first_name, 
                c.last_name, 
                comp.name as company, 
                c.email, 
                c.phone,
                (SELECT COUNT(DISTINCT i.id) FROM interactions i WHERE i.contact_id = c.id) as interaction_count,
                (SELECT COUNT(DISTINCT i.opportunity_id) FROM interactions i WHERE i.contact_id = c.id) as opportunity_count
            FROM contacts c
            LEFT JOIN companies comp ON c.company_id = comp.id
            GROUP BY c.id
            ORDER BY interaction_count DESC, opportunity_count DESC
        """
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            network = []
            for row in rows:
                name = f"{row[0] or ''} {row[1] or ''}".strip()
                network.append({
                    "name": name if name else "Unknown",
                    "company": row[2] or "N/A",
                    "email": row[3] or "N/A",
                    "phone": row[4] or "N/A",
                    "interactions": row[5] or 0,
                    "opportunities": row[6] or 0
                })
            return network

    def get_stale_cases(self, days_inactive: int) -> List[dict]:
        query = """
            WITH CaseActivity AS (
                SELECT 
                    oc.business_id,
                    c.name as company_name,
                    oc.status,
                    oc.updated_at as opp_updated_at,
                    MAX(i.interaction_date) as last_interaction_date
                FROM opportunity_cases oc
                LEFT JOIN companies c ON oc.company_id = c.id
                LEFT JOIN interactions i ON oc.id = i.opportunity_id
                WHERE oc.status NOT IN ('Closed', 'Offer')
                GROUP BY oc.id
            )
            SELECT 
                business_id,
                company_name,
                status,
                CAST(julianday('now') - julianday(MAX(IFNULL(opp_updated_at, '1970-01-01'), IFNULL(last_interaction_date, '1970-01-01'))) AS INTEGER) as days_inactive
            FROM CaseActivity
            WHERE days_inactive >= ?
            ORDER BY days_inactive DESC
        """
        with self.conn_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (days_inactive,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    "business_id": row[0],
                    "company": row[1] or "Unknown",
                    "status": row[2],
                    "days_inactive": row[3]
                })
            return results
