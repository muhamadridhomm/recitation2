from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    chunk_id: str
    source_document_id: str
    page_number: int
    text_content: str
    entropy_score: Optional[float] = Field(None, description="Model uncertainty score for L-RAG gating")
    vector_embedding_1024d: Optional[List[float]] = Field(None, description="Semantic vector for FAISS/pgvector search")

class SearchQuery(BaseModel):
    query_text: str
    use_lrag: bool = Field(True, description="Whether to apply entropy-based lazy loading")
    entropy_threshold: float = Field(0.5, description="Threshold to trigger deep vector search")
