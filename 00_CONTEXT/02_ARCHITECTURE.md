# Architecture

## Overview
CIOS is a local-first, offline-friendly executive career management system. It relies on a strict relational model, isolated from cloud dependencies, ensuring long-term maintainability, zero technical debt, and continuous user control (Human-in-the-loop). 

## Layers
1. **Input / Adapters:** Ingestion of raw data (PDF, URL, Manual).
2. **AI Core:** Extraction, Confidence Scoring, and Deduplication (Strictly scoped, non-autonomous).
3. **Domain:** Business logic and State Machines (Aggregate Root: `Opportunity Case`).
4. **Infrastructure:** Persistence via Repository Pattern and SQLite.

## Modules
- **Ingestion Pipeline:** Normalizes heterogeneous inputs.
- **AI Extraction Engine:** Identifies entities and scores confidence.
- **Opportunity Manager:** Handles the state machine and lifecycle.
- **Human Review Dashboard:** Forces manual approval before DB commit.

## Data Flow
`Input` -> `Adapter` -> `AI Extraction` -> `Confidence Analysis` -> `Duplicate Detection` -> `Human Review` -> `Database`.

## Opportunity Case
The Primary Aggregate Root. It represents a single employment opportunity across its complete lifecycle. 
**Strict Lifecycle:** `Detected` -> `Evaluating` -> `Preparing` -> `Applied` -> `Interview` -> `Offer` -> `Closed`.
*Rule: Transition to 'Closed' is permitted from any state. Backward transitions are blocked.*

## Repository Pattern
Abstracts the domain from persistence. The application layer interacts exclusively with `IOpportunityRepository`. No ORMs are used; pure SQL queries handle data hydration.

## SQLite
The Single Source of Truth for persistence. Relational structure. JSON columns are permitted strictly for storing `raw_ingestion_data` logs. Schema enforces `NOT NULL` constraints on all critical domain fields.

## Input Adapters
Polymorphic entry points (PDF, OCR, Email, URL, Text) that implement a standard `IInputAdapter` interface. They guarantee every source generates the exact same normalized dictionary prior to AI processing.

## Analytics
*Planned for Future Scope.* Will rely on raw SQL aggregations over the local SQLite database.

## Future Extensions
Any extension must pass the CIOS Governance filter:
1. Does it reduce complexity?
2. Does it improve maintainability?
3. Can it survive 5 years?
4. Is it compatible with SQLite/Local-first?