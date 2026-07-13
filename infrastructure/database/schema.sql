PRAGMA foreign_keys = ON;

-- 1. Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    website TEXT,
    industry TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Contacts Table
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

-- 3. Opportunity Cases Table
CREATE TABLE IF NOT EXISTS opportunity_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    company_id INTEGER,
    title TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('Detected', 'Evaluating', 'Preparing', 'Applied', 'Interview', 'Offer', 'Closed')
    ),
    confidence_score REAL CHECK (
        confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)
    ),
    raw_ingestion_data JSON,
    location TEXT,
    salary_min REAL,
    salary_max REAL,
    expires_at DATE,
    experience_required TEXT,
    source_platform VARCHAR,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
);

-- 4. CV Versions Table
CREATE TABLE IF NOT EXISTS cv_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Application Events Table
CREATE TABLE IF NOT EXISTS application_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    opportunity_id INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('Submission', 'InterviewScheduled', 'InterviewCompleted', 'OfferReceived', 'Rejected', 'Withdrawn', 'OfferDeclined', 'OfferAccepted')
    ),
    event_date DATETIME NOT NULL,
    cv_version_id INTEGER,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (cv_version_id) REFERENCES cv_versions(id) ON DELETE SET NULL
);

-- 6. Interactions Table
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    contact_id INTEGER, 
    opportunity_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL CHECK (
        interaction_type IN ('Email', 'Call', 'Meeting', 'LinkedIn', 'Other')
    ),
    interaction_date DATETIME NOT NULL,
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_cases(id) ON DELETE CASCADE
);

-- 7. Reminders Table
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    opportunity_id INTEGER,
    remind_at DATETIME NOT NULL,
    description TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK (
        is_completed IN (0, 1)
    ),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_cases(id) ON DELETE CASCADE
);

-- 8. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    opportunity_id INTEGER,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    document_type TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_cases(id) ON DELETE CASCADE
);

-- 9. Offers Table
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL UNIQUE,
    opportunity_id INTEGER NOT NULL,
    base_salary REAL,
    bonus_percentage REAL,
    equity_value REAL,
    benefits_summary TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunity_cases(id) ON DELETE CASCADE
);

-- --- INDEX STRATEGY ---

-- Limpieza de índices ineficientes/redundantes (necesario para actualizar DB viva si se corre el schema)
DROP INDEX IF EXISTS idx_interactions_contact_id;
DROP INDEX IF EXISTS idx_application_events_opportunity_id;
DROP INDEX IF EXISTS idx_opportunity_cases_status_updated;  -- nunca elegido por el planner (NOT IN fuerza SCAN, columna updated_at no ayuda)
DROP INDEX IF EXISTS idx_interactions_opportunity_id;        -- redundante: cubierto por idx_interactions_opp_date (prefijo izquierdo)

-- Índices base retenidos
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_cases_company_id ON opportunity_cases(company_id);
CREATE INDEX IF NOT EXISTS idx_opportunity_cases_status ON opportunity_cases(status);
CREATE INDEX IF NOT EXISTS idx_application_events_cv_version_id ON application_events(cv_version_id);
CREATE INDEX IF NOT EXISTS idx_reminders_opportunity_id ON reminders(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_documents_opportunity_id ON documents(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_offers_opportunity_id ON offers(opportunity_id);

-- Índices compuestos de optimización (Parche Claude - Fase 20, validados con EXPLAIN QUERY PLAN)
CREATE INDEX IF NOT EXISTS idx_interactions_opp_date ON interactions(opportunity_id, interaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_contact_opp ON interactions(contact_id, opportunity_id);
CREATE INDEX IF NOT EXISTS idx_application_events_opp_type ON application_events(opportunity_id, event_type);