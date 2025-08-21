"""
Pydantic schemas for RAG components.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentChunk(BaseModel):
    """Schema for a document chunk with metadata."""
    content: str = Field(..., description="The text content of the chunk")
    source: str = Field(..., description="Source document identifier")
    section: Optional[str] = Field(None, description="Section within the document")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    locale: str = Field(..., description="Language/locale code (es, en)")
    version_hash: str = Field(..., description="Content version hash for updates")
    updated_at: datetime = Field(..., description="Last update timestamp")
    pii: bool = Field(default=False, description="Contains personally identifiable information")
    chunk_index: int = Field(..., description="Index of chunk within parent document")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RetrievalResult(BaseModel):
    """Schema for retrieval results."""
    documents: List[DocumentChunk] = Field(..., description="Retrieved document chunks")
    scores: List[float] = Field(..., description="Relevance scores for each document")
    query: str = Field(..., description="Original query")
    total_found: int = Field(..., description="Total number of relevant documents found")
    retrieval_time_ms: int = Field(..., description="Time taken for retrieval in milliseconds")
    
    
class IngestionResult(BaseModel):
    """Schema for ingestion operation results."""
    success: bool = Field(..., description="Whether ingestion was successful")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    chunks_stored: int = Field(..., description="Number of chunks stored in vector DB")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    collection_name: str = Field(..., description="Target collection name")
    
    
class RetrieverConfig(BaseModel):
    """Configuration for the retriever."""
    k: int = Field(default=6, description="Number of documents to retrieve")
    score_threshold: Optional[float] = Field(default=None, description="Minimum similarity score")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant ID")
    locale: Optional[str] = Field(default=None, description="Filter by locale")
    search_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional search parameters")
