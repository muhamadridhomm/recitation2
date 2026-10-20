# Development Guidelines

## Architecture Overview
The system follows a strict three-tier service decomposition designed to decouple GPU-bound inference from CPU-bound orchestration.

1. **Gateway (Ingestion & Control):**
   - Stateless entry point built on FastAPI.
   - Issues Task IDs, persists raw images, maintains relational state.

2. **Worker (Pipeline Orchestration):**
   - Execution engine using Celery and Redis.
   - Handles I/O bound logic.
   - Uses **"Tiny Payload"** architecture: Workers pass lightweight file-path strings (e.g., `/tmp/page_5.pdf`) between tasks rather than heavy NumPy arrays to avoid GIL overhead and Redis memory pressure.

3. **Inference Service:**
   - Dedicated GPU tier (PaddleOCR / DocTR).
   - Must avoid the "Singleton Issue" by re-initializing models per process or managing multi-threaded inference safely.

## Tech Stack
- **Frontend:** SvelteKit, Tailwind CSS, D3.js (for Sankey diagrams).
- **Backend API:** Python, FastAPI.
- **Task Queue:** Celery, Redis.
- **Inference:** PaddleOCR, DocTR, HuggingFace embeddings (bge-m3 / multilingual-e5-small).
- **Database:** PostgreSQL (with FAISS for vectors) and/or SurrealDB for graph relationships.

## Lazy RAG (L-RAG) Philosophy
Standard RAG systems are "always-on," incurring high costs. This project enforces an entropy-based lazy loading pattern:
1. Attempt processing via compact document summaries first.
2. Calculate predictive uncertainty (entropy).
3. Only trigger expensive deep chunk retrieval if the uncertainty threshold ($\tau$) is exceeded.

## User-Triggered AI
Background processing for heavy tasks (like OCR) must only be triggered when a user explicitly requests a page or action, avoiding expensive batch-processing of unread volumes.
