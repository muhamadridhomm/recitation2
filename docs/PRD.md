# Product Requirements Document (PRD): Arabic Document Intelligence & Isnad Visualization

## Vision & Objective
An event-driven, cost-efficient, and highly scalable platform designed for Islamic scholarly research. The system aims to transform massive, unstructured multi-volume Arabic PDFs into highly structured, semantically searchable knowledge graphs. It prioritizes interactive visualizations (such as Isnad transmission chains) and specialized Arabic linguistic tooling, without incurring exorbitant AI inference costs, utilizing Lazy Retrieval-Augmented Generation (L-RAG).

## Target Audience
- Islamic scholars and researchers.
- Historians studying transmission chains (Ilm al-Rijal) and classical texts.
- Students requiring a distraction-free, RTL-optimized note-taking workspace.

## Core Features

1. **Event-Driven OCR Ingestion Pipeline:**
   - Asynchronous PDF processing utilizing a FastAPI, Celery, and Redis stack.
   - Decomposes massive documents into page-level tasks passing lightweight "tiny payloads" to avoid memory pressure.
   - Separate GPU inference tier (PaddleOCR/DocTR) from the CPU orchestration layer.

2. **Unified Search & Lazy-RAG (L-RAG) Engine:**
   - Hybrid search fusing BM25 full-text keyword indexing with 1024-dimensional semantic vectors.
   - Entropy-based gating mechanism: Queries trigger expensive LLM vector searches only when the model's uncertainty exceeds a configured threshold, saving API costs and latency.

3. **Database & Isnad Visualization:**
   - Hybrid SurrealDB / PostgreSQL+FAISS architecture.
   - Interactive D3-sankey diagrams mapping over 100,656 parsed chains and 115,735 narrator profiles.
   - Color-coded node grading based on narrator reliability (e.g., Thiqah, Da'if).
   - Genealogy resolution utilizing 76 relational rules to disambiguate classical names.

4. **Frontend Scholar Workspace:**
   - SvelteKit-based, RTL-optimized distraction-free interface.
   - **Hadith Diff:** Word-level divergence tracking across transmission chains.
   - **Smart Notes:** Video timestamping, PDF annotations, and automatic insertion of diacritics/honorifics.
   - **Dual-Stemmer:** Bridge between Quranic roots and the Hadith corpus.

## Non-Functional Requirements
- **Performance:** Asynchronous processing guarantees that massive uploads don't block the ingestion gateway.
- **Cost-Efficiency:** Strict adherence to L-RAG and user-triggered AI features to minimize unnecessary LLM tokens.
- **Transparency:** The UI explicitly flags AI-generated text as "Unverified Draft" until human review.
