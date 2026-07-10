# CIOS (Career Intelligence Operating System)

## Purpose
A permanent, local-first foundation for executive career management, ensuring complete data ownership and human-in-the-loop AI assistance.

## Architecture Overview
CIOS follows Clean Architecture principles, utilizing the Repository Pattern to decouple the core domain logic from the SQLite infrastructure. The system models `OpportunityCase` as the primary aggregate root through a strict state machine lifecycle.

## Folder Map
- `00_CONTEXT/`: Master memory, rules, and system identity.
- `config/`: Configuration templates.
- `core/`: Application logic and pipelines.
- `data/`: Local storage (database, inbox, attachments, etc.).
- `docs/`: Technical documentation.
- `domain/`: Core business models and interfaces.
- `infrastructure/`: Database schemas, repositories, and external adapters.
- `logs/`, `temp/`, `cache/`: Runtime directories.
- `scripts/`: Utilities for system maintenance.

## Current Status
Phase 2/3 (Database & Core Engine Bootstrap)

## Development Philosophy
- Local First & Single Source of Truth.
- Strict Domain-Infrastructure separation.
- Zero over-engineering.

## Roadmap Summary
- Phase 1: Architecture & Refinement
- Phase 2: Database Initialization
- Phase 3: Core Engine & Ingestion Pipeline
- Phase 4: Input Adapters & Dashboard
- Phase 5: AI Intelligence

## Contributing Rules
- Preserve all existing documentation and context.
- Read `00_CONTEXT/09_MASTER_MEMORY.md` before coding.

## AI Collaboration Workflow
- Enforce strict adherence to approved design decisions.
- Follow M2M Instruction Batches for execution sequences.
