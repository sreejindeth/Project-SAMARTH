## Loom Recording Outline (120s)

1. **Intro (0–20s)**
   - State the challenge goal: Q&A across agriculture + climate datasets from data.gov.in with citations.
   - Highlight offline-friendly architecture.

2. **Data Workflow (20–50s)**
   - Show `docs/DATASETS.md` and explain selected resource IDs.
   - Quickly open `data/raw/` (if populated) to emphasise snapshotting.

3. **Architecture (50–75s)**
   - Display `docs/ARCHITECTURE.md` mermaid diagram or explain stack (FastAPI + pandas + DuckDB-ready + static UI).

4. **Live Demo (75–110s)**
   - Run backend (`uvicorn app.main:app --reload`).
   - Fire a sample query in the frontend (rainfall comparison).
   - Trigger another query (policy arguments) highlighting correlation, tables, citations.

5. **Close (110–120s)**
   - Mention extensibility (add datasets via config) and privacy (no external LLM).
   - Link to README for setup + further work.

