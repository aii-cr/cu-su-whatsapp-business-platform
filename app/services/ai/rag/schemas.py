"""
Pydantic schemas for RAG components.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class RetrievalMethod(str, Enum):
    """Retrieval methods for the hybrid retriever."""
    DENSE = "dense"
    HYBRID = "hybrid"
    SPARSE = "sparse"


class DocumentChunk(BaseModel):
    """Schema for a document chunk with metadata."""
    content: str = Field(..., description="The text content of the chunk")
    source: str = Field(..., description="Source document identifier")
    section: Optional[str] = Field(None, description="Section within the document")
    subsection: Optional[str] = Field(None, description="Subsection within the document")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    locale: str = Field(..., description="Language/locale code (es, en)")
    version_hash: str = Field(..., description="Content version hash for updates")
    updated_at: datetime = Field(..., description="Last update timestamp")
    pii: bool = Field(default=False, description="Contains personally identifiable information")
    chunk_index: int = Field(..., description="Index of chunk within parent document")
    
    # Enhanced metadata for hybrid retrieval
    doc_id: Optional[str] = Field(None, description="Unique document identifier")
    title: Optional[str] = Field(None, description="Document title")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    price_crc: Optional[float] = Field(None, description="Price in Costa Rican Colones")
    price_text: Optional[str] = Field(None, description="Price as text")
    url: Optional[str] = Field(None, description="Related URL")
    contact_value: Optional[str] = Field(None, description="Contact information")
    channel_number: Optional[str] = Field(None, description="Channel number for TV/radio")
    is_faq: bool = Field(default=False, description="Whether this is an FAQ entry")
    is_promo: bool = Field(default=False, description="Whether this is a promotional entry")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RetrievalResult(BaseModel):
    """Schema for retrieval results."""
    documents: List[DocumentChunk] = Field(..., description="Retrieved document chunks")
    scores: List[float] = Field(..., description="Relevance scores for each document")
    query: str = Field(..., description="Original query")
    expanded_queries: List[str] = Field(default_factory=list, description="Expanded queries used")
    total_found: int = Field(..., description="Total number of relevant documents found")
    retrieval_time_ms: int = Field(..., description="Time taken for retrieval in milliseconds")
    method: RetrievalMethod = Field(default=RetrievalMethod.DENSE, description="Retrieval method used")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters applied during retrieval")
    threshold_used: Optional[float] = Field(None, description="Score threshold used")
    metadata_overrides: int = Field(default=0, description="Number of below-threshold items kept due to metadata")


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
    """Configuration for the hybrid retriever."""
    k: int = Field(default=10, description="Number of documents to retrieve")
    score_threshold: Optional[float] = Field(default=0.20, description="Minimum similarity score")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant ID")
    locale: Optional[str] = Field(default="es_CR", description="Filter by locale")
    method: RetrievalMethod = Field(default=RetrievalMethod.DENSE, description="Retrieval method")
    search_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Additional search parameters")
    
    # Multi-query expansion settings
    enable_multi_query: bool = Field(default=True, description="Enable multi-query expansion")
    max_expanded_queries: int = Field(default=3, description="Maximum number of expanded queries")
    
    # Compression settings
    enable_compression: bool = Field(default=True, description="Enable result compression")
    compression_threshold: float = Field(default=0.15, description="Similarity threshold for compression")
    max_final_chunks: int = Field(default=6, description="Maximum chunks after compression")
    
    # Qdrant-specific settings
    ef: int = Field(default=96, description="Qdrant search parameter ef")
    enable_metadata_override: bool = Field(default=True, description="Keep below-threshold items with matching metadata")


class MultiQueryConfig(BaseModel):
    """Configuration for multi-query expansion."""
    enable_numeric_expansion: bool = Field(default=True, description="Expand numeric values")
    enable_synonym_expansion: bool = Field(default=True, description="Expand synonyms")
    enable_accent_normalization: bool = Field(default=True, description="Normalize accents")
    max_expanded_queries: int = Field(default=3, description="Maximum number of expanded queries")
    
    # Spanish-specific expansions
    spanish_synonyms: Dict[str, List[str]] = Field(default_factory=lambda: {
        "precio": ["costo", "tarifa", "valor"],
        "telefonía": ["VoIP", "línea fija", "teléfono"],
        "horario": ["horario administrativo", "atención", "disponibilidad"],
        "IPTV": ["televisión por Internet", "lista de canales", "TV digital"],
        "cobertura": ["zona", "área", "disponibilidad"],
        "plan": ["paquete", "servicio", "oferta"],
        "internet": ["conexión", "banda ancha", "WiFi"],
        "móvil": ["celular", "teléfono móvil", "smartphone"]
    })
    
    # Numeric expansions
    numeric_patterns: Dict[str, List[str]] = Field(default_factory=lambda: {
        r"(\d+)/(\d+)\s*Gbps": ["{0} Gbps simétrico", "{0}/{1} Gbps", "{0} Gbps de bajada, {1} Gbps de subida"],
        r"(\d+)\s*Mbps": ["{0} Mbps", "{0} megabits por segundo"],
        r"(\d+)\s*GB": ["{0} GB", "{0} gigabytes", "{0} gigas"],
        r"₡(\d+)": ["{0} colones", "{0} CRC", "₡{0}"]
    })


class CompressionConfig(BaseModel):
    """Configuration for result compression."""
    similarity_threshold: float = Field(default=0.15, description="Similarity threshold for filtering")
    max_chunks: int = Field(default=6, description="Maximum chunks after compression")
    enable_reordering: bool = Field(default=True, description="Enable long context reordering")
    reorder_window: int = Field(default=3, description="Window size for reordering")
