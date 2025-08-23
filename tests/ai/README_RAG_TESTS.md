# RAG Testing Suite

This directory contains comprehensive tests for the RAG (Retrieval-Augmented Generation) system used in the WhatsApp Business API chatbot.

## Test Files

### 1. `test_rag_comprehensive.py` - Comprehensive RAG Testing with RAGAS
**Purpose**: Full evaluation using RAGAS metrics for production-ready testing
**Features**:
- 19 test queries across 8 categories
- RAGAS evaluation metrics (context_relevancy, faithfulness, answer_relevancy, context_recall)
- Ground truth comparison
- Detailed performance analysis
- JSON result export

**Usage**:
```bash
python tests/ai/test_rag_comprehensive.py
```

**Requirements**:
```bash
pip install ragas datasets
```

### 2. `test_rag_basic.py` - Basic RAG Testing
**Purpose**: Simple functionality testing without external dependencies
**Features**:
- 5 core test queries
- Basic relevance scoring
- Performance metrics
- JSON result export

**Usage**:
```bash
python tests/ai/test_rag_basic.py
```

### 3. `test_rag_interactive.py` - Interactive RAG Testing
**Purpose**: Manual testing of individual queries with detailed output
**Features**:
- Interactive query input
- Real-time results display
- Detailed analysis per query
- Perfect for debugging and exploration

**Usage**:
```bash
python tests/ai/test_rag_interactive.py
```

## Test Categories

The tests cover the following categories:

| Category | Description | Example Queries |
|----------|-------------|-----------------|
| **Pricing** | Service costs and pricing information | "¿Cuál es el precio del plan de 500 Mbps?" |
| **Service Info** | Service details and features | "¿Qué incluye el plan de 1 Gbps?" |
| **Contact** | Contact information and support | "¿Cuál es el número de WhatsApp?" |
| **Installation** | Setup and installation processes | "¿Cuánto tiempo toma la instalación?" |
| **Payment** | Payment methods and processing | "¿Qué métodos de pago aceptan?" |
| **Technical** | Technical specifications | "¿Los planes son simétricos?" |
| **Company** | Company information | "¿Quién es ADN?" |
| **Privacy** | Privacy and data protection | "¿Qué datos recopilan?" |

## Performance Metrics

### Basic Metrics
- **Success Rate**: Percentage of successful retrievals
- **Latency**: Response time in milliseconds
- **Results Count**: Number of documents retrieved

### Quality Metrics
- **Relevance Score**: 0.0-1.0 based on keyword matches and content quality
- **Content Quality**: poor/fair/good/excellent based on content length
- **Section Match**: Whether retrieved content matches expected section

### RAGAS Metrics (Comprehensive Test)
- **Context Relevancy**: How relevant the retrieved context is to the question
- **Faithfulness**: How faithful the generated answer is to the retrieved context
- **Answer Relevancy**: How relevant the generated answer is to the question
- **Context Recall**: How much of the relevant information is captured

## Dataset

Tests use the `adn_rag_base_full_v1_3.csv` dataset containing:
- 162 documents across multiple sections
- Pricing information for residential and business plans
- Service details (IPTV, VoIP, etc.)
- Contact and support information
- Company and privacy information

## Setup Requirements

### Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install langchain langchain-openai langchain-qdrant qdrant-client
```

### For RAGAS Testing
```bash
pip install ragas datasets
```

### Configuration
Ensure the following environment variables are set:
- `OPENAI_API_KEY`
- `QDRANT_URL`
- `QDRANT_API_KEY`

## Running Tests

### Quick Test (Recommended)
```bash
python tests/ai/test_rag_basic.py
```

### Full Evaluation with RAGAS
```bash
python tests/ai/test_rag_comprehensive.py
```

### Interactive Testing
```bash
python tests/ai/test_rag_interactive.py
```

## Expected Results

### Success Criteria
- **Basic Test**: >80% success rate
- **Comprehensive Test**: >70% success rate with RAGAS scores >0.7
- **Latency**: <5 seconds average
- **Relevance**: >0.6 average relevance score

### Sample Output
```
📊 BASIC RAG TEST SUMMARY
==========================================
📈 Basic Performance:
  Total tests: 5
  Successful: 4
  Failed: 1
  Success rate: 80.0%

⏱️  Performance Metrics:
  Average latency: 4156.23ms
  Min latency: 3245.12ms
  Max latency: 5234.67ms

🎯 Content Quality Analysis:
  Average relevance score: 0.779
  High relevance (>0.8): 2
  Medium relevance (0.5-0.8): 2
  Low relevance (<0.5): 1

🎉 EXCELLENT: RAG system is working well!
```

## Troubleshooting

### Common Issues

1. **Qdrant Connection Error**
   - Verify Qdrant URL and API key
   - Check network connectivity

2. **OpenAI API Error**
   - Verify OpenAI API key
   - Check API quota and limits

3. **RAGAS Import Error**
   - Install with: `pip install ragas datasets`
   - Check Python version compatibility

4. **Collection Index Error**
   - Tests automatically recreate collections
   - Check Qdrant permissions

### Debug Mode
For detailed debugging, use the interactive test:
```bash
python tests/ai/test_rag_interactive.py
```

## Result Files

Tests generate timestamped JSON result files:
- `rag_basic_test_results_YYYYMMDD_HHMMSS.json`
- `rag_test_results_YYYYMMDD_HHMMSS.json` (comprehensive)

These files contain:
- Test results with detailed metrics
- Query analysis
- Performance data
- RAGAS evaluation results (comprehensive test)

## Integration with CI/CD

The basic test can be integrated into CI/CD pipelines:
```yaml
- name: Run RAG Tests
  run: |
    python tests/ai/test_rag_basic.py
    # Check exit code for pass/fail
```

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add appropriate test categories
3. Include ground truth for comprehensive tests
4. Update this README with new features
5. Ensure tests are deterministic and repeatable
