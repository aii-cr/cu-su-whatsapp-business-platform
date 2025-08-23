# Hybrid-Ready, Dense-First Retriever Implementation

## Overview

This implementation replaces the previous ParentDocumentRetriever approach with a sophisticated hybrid-ready, dense-first retriever optimized for short, structured CSV rows (Spanish locale). The new system provides improved recall on terse queries, precision on prices/phones/horarios, and reduces low-score misses.

## Key Features

### 🚀 **Multi-Query Expansion**
- **Spanish Synonym Expansion**: Automatically expands queries using Spanish synonyms
  - `precio` ↔ `costo` ↔ `tarifa`
  - `telefonía` ↔ `VoIP` ↔ `línea fija`
  - `horario` ↔ `horario administrativo` ↔ `atención`
  - `IPTV` ↔ `televisión por Internet` ↔ `lista de canales`

- **Numeric Pattern Expansion**: Expands numeric patterns for better matching
  - `1/1 Gbps` ↔ `1 Gbps simétrico`
  - `500/500 Mbps` ↔ `500 Mbps simétrico`
  - `₡15000` ↔ `15000 colones`

- **Accent Normalization**: Handles Spanish accents for better matching
  - `telefonia` ↔ `telefonía`

### 🎯 **Enhanced Metadata Filtering**
- **Required Filters**: `tenant_id`, `locale=es_CR`
- **Intent-Based Filters**: Automatic section/tag filtering based on query keywords
- **Metadata Override**: Keeps below-threshold items with matching metadata

### 📊 **Result Compression & Reordering**
- **EmbeddingsFilter**: Filters results by similarity threshold (0.15)
- **Smart Reordering**: Prioritizes FAQ entries, price information, contact details
- **Context Optimization**: Limits final context to ≤6 chunks for LLM

### 🔧 **One-Row-One-Document Approach**
- **Canonical Text Layout**: Structured document format
- **Enhanced Metadata**: Rich metadata extraction (prices, URLs, contact info)
- **Stable Document IDs**: Consistent document identification

## Architecture

### Core Components

```
app/services/ai/rag/
├── retriever.py          # Main hybrid retriever implementation
├── ingest.py            # Enhanced ingestion with canonical layout
├── schemas.py           # Updated schemas for hybrid features
└── __init__.py          # Module exports
```

### Key Classes

#### `HybridRetriever`
- Main retriever class with multi-query expansion and compression
- Supports dense, hybrid, and sparse retrieval methods
- Configurable parameters for k, score threshold, ef, etc.

#### `MultiQueryExpander`
- Handles query expansion using Spanish synonyms and patterns
- Configurable expansion strategies
- Accent normalization support

#### `ResultCompressor`
- Filters and reorders retrieval results
- Uses embeddings similarity for filtering
- Smart reordering based on metadata relevance

## Configuration

### Retriever Configuration

```python
from app.services.ai.rag.retriever import build_retriever
from app.services.ai.rag.schemas import RetrievalMethod

retriever = build_retriever(
    tenant_id="default",
    locale="es_CR",
    k=10,                    # Number of documents to retrieve
    score_threshold=0.20,    # Minimum similarity score
    method=RetrievalMethod.DENSE,
    enable_multi_query=True,     # Enable query expansion
    enable_compression=True      # Enable result compression
)
```

### Multi-Query Configuration

```python
from app.services.ai.rag.schemas import MultiQueryConfig

config = MultiQueryConfig(
    enable_numeric_expansion=True,
    enable_synonym_expansion=True,
    enable_accent_normalization=True,
    max_expanded_queries=3
)
```

### Compression Configuration

```python
from app.services.ai.rag.schemas import CompressionConfig

config = CompressionConfig(
    similarity_threshold=0.15,
    max_chunks=6,
    enable_reordering=True,
    reorder_window=3
)
```

## Usage Examples

### Basic Retrieval

```python
from app.services.ai.rag.retriever import build_retriever

# Build retriever
retriever = build_retriever(
    tenant_id="default",
    locale="es_CR"
)

# Retrieve documents
result = await retriever.get_retrieval_result("precio IPTV")

print(f"Found {len(result.documents)} documents")
print(f"Expanded queries: {result.expanded_queries}")
print(f"Retrieval time: {result.retrieval_time_ms}ms")
```

### Integration with RAG Tool

```python
from app.services.ai.agents.whatsapp.tools.rag_tool import RAGTool

# Initialize RAG tool with hybrid retriever
rag_tool = RAGTool()

# Execute RAG search
result = await rag_tool.execute_with_timeout(
    query="precio telefonía",
    tenant_id="default",
    locale="es_CR",
    use_hybrid_retriever=True  # Enable new hybrid retriever
)

if result.status == "success":
    print(f"Answer: {result.data['answer']}")
    print(f"Confidence: {result.data['confidence']}")
    print(f"Sources: {len(result.data['sources'])}")
```

### Integration with LangGraph

```python
from app.services.ai.agents.whatsapp.graphs.subgraphs.faq_rag_flow import run_hybrid_rag_flow

# Use in LangGraph state
state = {
    "user_text": "precio IPTV",
    "conversation_id": "123",
    "customer_language": "es_CR"
}

# Execute hybrid RAG flow
updated_state = await run_hybrid_rag_flow(state)

print(f"Reply: {updated_state['reply']}")
print(f"Confidence: {updated_state['confidence']}")
```

## Data Ingestion

### Canonical Text Layout

The new ingestion system creates documents with this structure:

```
[Plan Internet 500/500 Mbps]
Internet > Planes Residenciales
Velocidad simétrica de 500 Mbps de bajada y subida
tags: internet, residencial, simétrico
precio: ₡25000
https://example.com/plan-500 | +506 2222-2222
```

### Enhanced Metadata Extraction

- **Title**: Extracted from title/name/plan columns
- **Section/Subsection**: Hierarchical organization
- **Tags**: Automatic extraction from tags and category columns
- **Price**: Numeric and text price extraction with ₡ symbol
- **Contact**: URLs, phone numbers, emails
- **Flags**: FAQ and promotional content identification

### Payload Indexes

The system creates efficient indexes for:
- `tenant_id` (KEYWORD)
- `locale` (KEYWORD)
- `section` (KEYWORD)
- `subsection` (KEYWORD)
- `tags` (KEYWORD)
- `doc_id` (KEYWORD)
- `is_faq` (BOOL)
- `is_promo` (BOOL)

## Performance Characteristics

### Retrieval Performance
- **Median Latency**: <250ms (target)
- **Query Expansion**: 2-3 variants per query
- **Compression**: Reduces results to ≤6 chunks
- **Filtering**: Strong metadata filters for precision

### Quality Metrics
- **Recall**: Improved on terse Spanish queries
- **Precision**: Enhanced for price/contact/horario queries
- **Fallback Handling**: Metadata override for relevant low-score items

## Testing

### Test Script

Run the comprehensive test suite:

```bash
python test_hybrid_retriever.py
```

### Test Cases

The test suite validates:

1. **Query Expansion**
   - `precio IPTV` → IPTV price information
   - `horario administrativo` → admin hours
   - `telefonía precio` → phone pricing
   - `telefonia precio` → accent normalization

2. **Performance**
   - Median latency <250ms
   - Query expansion effectiveness
   - Compression efficiency

3. **Quality**
   - ≥90% success rate on test queries
   - Proper metadata filtering
   - Fallback handling

### Acceptance Criteria

- ✅ **≥90%** of test queries produce correct results
- ✅ **Median latency <250ms** for retrieval
- ✅ **No hallucinated prices/phones** (values match payload)
- ✅ **Proper fallback handling** for low-confidence results

## Migration from Legacy System

### Backward Compatibility

The system maintains backward compatibility:

```python
# Legacy code continues to work
from app.services.ai.rag.retriever import EnhancedParentDocumentRetriever

# New code uses hybrid retriever
from app.services.ai.rag.retriever import HybridRetriever
```

### Feature Flags

Control retriever behavior:

```python
# Use new hybrid retriever (default)
rag_tool.execute_with_timeout(
    query="test",
    use_hybrid_retriever=True
)

# Use legacy retriever
rag_tool.execute_with_timeout(
    query="test",
    use_hybrid_retriever=False
)
```

## Telemetry & Monitoring

### Retrieval Metrics

The system logs comprehensive metrics:

```python
{
    "method": "dense",
    "expanded_queries": ["precio IPTV", "costo IPTV", "tarifa IPTV"],
    "filters_applied": {"tenant_id": "default", "locale": "es_CR"},
    "threshold_used": 0.20,
    "metadata_overrides": 1,
    "retrieval_time_ms": 180
}
```

### Performance Monitoring

- Query expansion effectiveness
- Compression ratios
- Filter performance
- Latency distributions

## Future Enhancements

### Phase 2: Hybrid Fusion
- **BM25 Integration**: Add sparse retrieval
- **RRF Fusion**: Reciprocal Rank Fusion
- **Cross-Encoder Reranking**: Spanish-capable reranker

### Phase 3: Advanced Features
- **Dynamic Filtering**: Query-aware filter selection
- **Adaptive Compression**: Query-dependent compression
- **A/B Testing**: Feature flag management

## Troubleshooting

### Common Issues

1. **No Documents Found**
   - Check collection health: `await check_collection_health()`
   - Verify ingestion: `await ingest_documents()`
   - Check filters: Ensure tenant_id and locale are correct

2. **High Latency**
   - Reduce `k` parameter
   - Disable compression temporarily
   - Check Qdrant performance

3. **Low Quality Results**
   - Adjust `score_threshold`
   - Enable/disable multi-query expansion
   - Review metadata filtering

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("app.services.ai.rag").setLevel(logging.DEBUG)
```

## API Reference

### HybridRetriever

```python
class HybridRetriever:
    async def aget_relevant_documents(query: str) -> List[Document]
    async def get_retrieval_result(query: str) -> RetrievalResult
    async def health_check() -> Dict[str, Any]
```

### RetrievalResult

```python
class RetrievalResult:
    documents: List[DocumentChunk]
    scores: List[float]
    query: str
    expanded_queries: List[str]
    method: RetrievalMethod
    filters_applied: Dict[str, Any]
    threshold_used: Optional[float]
    metadata_overrides: int
    retrieval_time_ms: int
```

### DocumentChunk

```python
class DocumentChunk:
    content: str
    source: str
    section: Optional[str]
    subsection: Optional[str]
    tenant_id: str
    locale: str
    doc_id: Optional[str]
    title: Optional[str]
    tags: List[str]
    price_crc: Optional[float]
    price_text: Optional[str]
    url: Optional[str]
    contact_value: Optional[str]
    is_faq: bool
    is_promo: bool
```

## Contributing

When contributing to the hybrid retriever:

1. **Follow the schema-first approach**
2. **Add comprehensive tests** for new features
3. **Update telemetry** for new metrics
4. **Maintain backward compatibility**
5. **Document configuration changes**

## License

This implementation is part of the WhatsApp Business Platform Backend project.
