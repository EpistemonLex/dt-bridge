# dt-bridge: The Frontal Lobe Blueprint (Mac Studio)
**Version:** 1.0 (2026-03-06)  
**Status:** Active Development  

## Vision
The **dt-bridge** (Frontal Lobe) is the high-rank orchestrator of the Deepthought Educational OS. Residing on the Mac Studio (The Principal), it transforms raw, static educational data from the Kolibri ecosystem into proactive, AI-tutored intelligence payloads. It is the "brain" that bridges ground-truth pedagogy with active heutagogical creation.

## Core Mandates
1. **Pure Kolibri Ingestion**: Anchor all curriculum logic to native Kolibri Topic Trees and ContentNodes. Purge external bureaucratic standards (TEKS, etc.) in favor of the inherent pedagogical structure of the curated content.
2. **Multi-Agent Reasoning**: Utilize LangGraph to coordinate a "Roundtable" of specialized agents (Librarian, Assessor, Foreman) to synthesize lesson plans.
3. **Hybrid Topology**: 
    - **KuzuDB**: Manages the rigid, hierarchical structure (Topic Trees) and prerequisites.
    - **LanceDB**: Manages the fluid, semantic memory (Transcripts and Vectors) for RAG.
4. **Flow**: Operate under a strict **Spec -> TDD -> Implementation** cycle managed by the LangGraph orchestrator.

## Architectural Components

### 1. The ETL Pipeline (`src/dt_bridge/etl/`)
- **KolibriTopicExtractor**: Recursively traverses Kolibri's channel SQLite databases to build the KuzuDB graph.
- **TranscriptVectorizer**: Locates `.vtt` transcripts in Kolibri's content storage, chunks them, and ingests them into LanceDB vector stores.

### 2. The Agent Roundtable (`src/dt_bridge/agents/`)
- **The Librarian**: Queries LanceDB for the exact semantic context (transcripts, vocabulary) required for a lesson.
- **The Assessor**: Analyzes student telemetry (synced from The Backpack) to identify cognitive gaps.
- **The Foreman**: Coordinates with the Factory Forge (Desktop PC) to generate bespoke S.T.E.A.M. coding sandboxes.

### 3. Middleware Contract (`dt-contracts`)
- Every output from the Frontal Lobe must strictly adhere to the `HybridLessonPlan` Pydantic models.
- Ensures cross-node compatibility between the Mac Studio, PC Forge, and Chromebook Backpacks.

## Data Flow
1. **Sync In**: Ingest Kolibri DBs and Backpack Telemetry.
2. **Transform**: Update KuzuDB topology and LanceDB vector space.
3. **Reason**: LangGraph Roundtable evaluates the student's edge and the curriculum ground truth.
4. **Sync Out**: Distribute `HybridLessonPlan` JSON payloads to edge devices.

## Roadmap (Immediate Phase)
- [x] Initialize Git and GitHub Repository.
- [x] Implement `KolibriTopicExtractor` (KuzuDB).
- [x] Implement `TranscriptVectorizer` (LanceDB).
- [x] Finalize LangGraph `Librarian` node integration.
- [x] Implement `Assessor` node to consume `dt-contracts` telemetry schemas.
- [x] Integrate full multi-agent Roundtable (Librarian, Assessor, Foreman).
