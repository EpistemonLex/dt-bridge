# dt-bridge: The Frontal Lobe Blueprint (Mac Studio)
**Version:** 1.0 (2026-03-06)  
**Status:** Active Development  

## Vision
The **dt-bridge** is a standalone **Kolibri Graph RAG Repository**. It serves as a specialized knowledge base that extracts, structures, and indexes the entirety of Kolibri's educational content (Topic Trees, Transcripts, and Metadata). It acts as a dedicated data layer for the **Deepthought Server**, allowing the server's multi-agent engine (AG2) to "see" and "map" Kolibri resources with high fidelity.

## Core Mandates
1. **Pure Kolibri Ingestion**: Anchor all curriculum logic to native Kolibri Topic Trees and ContentNodes. 
2. **Standalone Repository**: Maintain a dedicated instance of KuzuDB (Topology) and LanceDB (Semantic Memory) specifically for Kolibri ground truth.
3. **Retrieval Service**: Provide a robust "Librarian" interface for external consumers (like Deepthought Server) to query the Kolibri Graph and Vector space.
4. **Separation of Concerns**: The Bridge handles **Data and Retrieval**; the Deepthought Server handles **Reasoning and Orchestration**.

## Architectural Components

### 1. The ETL Pipeline (`src/dt_bridge/etl/`)
- **KolibriTopicExtractor**: Recursively traverses Kolibri's channel SQLite databases to build the KuzuDB graph.
- **TranscriptVectorizer**: Locates `.vtt` transcripts in Kolibri's content storage, chunks them, and ingests them into LanceDB vector stores.

### 2. The Librarian Service (`src/dt_bridge/retrieval/`)
- **Graph Traversal**: Tools to query KuzuDB for parent/child relationships, prerequisite mappings, and topic clusters.
- **Semantic Search**: Tools to query LanceDB for relevant transcript chunks based on student objectives.
- **Metadata Provider**: Returns strictly validated `dt-contracts` objects for Kolibri resources.

### 3. Middleware Contract (`dt-contracts`)
- Every output from the Bridge must strictly adhere to the `dt-contracts` models to ensure the main server can ingest them without transformation.

## Data Flow
1. **Bridge** extracts Kolibri metadata and text.
2. **Bridge** populates its internal KuzuDB/LanceDB stores.
3. **Deepthought Server** queries the Bridge Librarian tool during agent workflows.
4. **Deepthought Server** maps the returned Kolibri resources into its own lesson plans.

## Roadmap (Immediate Phase)
- [x] Initialize Git and GitHub Repository.
- [x] Implement `KolibriTopicExtractor` (KuzuDB).
- [x] Implement `TranscriptVectorizer` (LanceDB).
- [x] Finalize LangGraph `Librarian` node integration.
- [x] Implement `Assessor` node to consume `dt-contracts` telemetry schemas.
- [x] Integrate full multi-agent Roundtable (Librarian, Assessor, Foreman).
