CREATE TABLE IF NOT EXISTS opportunity_cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Detected', 'Evaluating', 'Preparing', 'Applied', 'Interview(s)', 'Offer', 'Closed')),
    confidence_score REAL,
    raw_ingestion_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
