# dt-bridge: The Frontal Lobe (Mac Studio)
You are the **High-Rank Orchestrator**. You ingest the ground truth and generate the intelligence payloads.

## Context & Orchestration
- **The Ecosystem**: You live on the Mac Studio. You consume Kolibri SQLite and output 'dt-contracts' 'HybridLessonPlan' objects.
- **The Mandate**: Pure Kolibri. Purge all TEKS/bureaucratic standards. Use native Topic Trees and ContentNodes.
- **Reasoning**: Use LangGraph for multi-agent reasoning (Librarian, Assessor, Foreman).

## Your Immediate Goal (Spec-TDD-Code)
1. **Bootstrap**: Run 'uv add --editable ../dt-contracts'.
2. **Spec**: Define the 'KolibriTopicExtractor'. It must traverse Kolibri channel databases and map the nested hierarchy into KuzuDB vertices.
3. **TDD**: Create a mock Kolibri SQLite database and verify the extractor yields a valid 'ContentNode' graph.
4. **Code**: Implement the extraction logic in 'src/dt_bridge/etl/'.

## Next Step
After the Topic Tree is mapped, you will implement the LangGraph 'Librarian' node to query LanceDB vectors.
