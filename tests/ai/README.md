# AI Agent Tests

This directory contains all tests related to the AI agent functionality for the WhatsApp Business Platform.

## 📁 Directory Structure

```
tests/ai/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── run_all_tests.py              # Comprehensive test runner
├── test_ai_agent.py              # AI agent functionality tests
├── test_conversation_context.py  # Conversation context and memory tests
└── setup/
    ├── __init__.py               # Setup package initialization
    └── setup_ai_agent.py         # AI agent setup and initialization
```

## 🧪 Test Categories

### 1. Setup Tests (`setup/`)
- **Purpose**: Verify AI agent environment and dependencies
- **Files**: `setup_ai_agent.py`
- **Tests**:
  - Environment variable validation
  - AI dependency availability
  - Knowledge base initialization
  - Agent service setup

### 2. Conversation Context Tests
- **Purpose**: Test conversation memory and context management
- **Files**: `test_conversation_context.py`
- **Tests**:
  - Memory service functionality
  - Conversation history management
  - Session data handling
  - Memory statistics
  - Context retrieval and clearing

### 3. AI Agent Tests
- **Purpose**: Test AI agent processing and response generation
- **Files**: `test_ai_agent.py`
- **Tests**:
  - Agent health checks
  - Knowledge base health
  - Message processing
  - Response generation
  - Language detection
  - Intent classification

### 4. Integration Tests
- **Purpose**: Test complete AI system workflows
- **Files**: `run_all_tests.py` (includes integration tests)
- **Tests**:
  - End-to-end conversation flow
  - Memory persistence across interactions
  - Agent service integration
  - Error handling and recovery

## 🚀 Running Tests

### Run All Tests
```bash
# Run comprehensive test suite
python tests/ai/run_all_tests.py
```

### Run Individual Test Categories
```bash
# Setup tests only
python tests/ai/setup/setup_ai_agent.py

# Conversation context tests only
python tests/ai/test_conversation_context.py

# AI agent tests only
python tests/ai/test_ai_agent.py
```

### Run with Pytest
```bash
# Run all AI tests with pytest
python -m pytest tests/ai/

# Run specific test file
python -m pytest tests/ai/test_ai_agent.py

# Run with verbose output
python -m pytest tests/ai/ -v
```

## 🔧 Prerequisites

Before running AI tests, ensure:

1. **Environment Setup**:
   ```bash
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   uv sync
   ```

2. **Environment Variables**:
   ```bash
   # Required in .env file
   OPENAI_API_KEY=your_openai_api_key
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_api_key
   MONGODB_URI=your_mongodb_uri
   LANGCHAIN_API_KEY=your_langsmith_api_key
   ```

3. **Database Connection**:
   - MongoDB instance running
   - Qdrant vector database accessible

## 📊 Test Results

The comprehensive test runner provides detailed output including:

- ✅ **Setup Status**: Environment and dependency validation
- 🧠 **Memory Tests**: Conversation context and memory management
- 🤖 **Agent Tests**: AI processing and response generation
- 🔗 **Integration Tests**: End-to-end workflow validation

### Expected Output
```
🚀 Starting Comprehensive AI Agent Tests...
============================================================

🔧 Running AI Agent Setup Tests...
==================================================
✅ Environment configuration looks good!
✅ AI dependencies are available!
✅ Knowledge base initialized successfully!
✅ Setup tests completed successfully

🧠 Running Conversation Context Tests...
==================================================
✅ Memory service imported successfully
✅ Conversation memory created successfully
✅ Session data updated successfully
✅ Conversation context tests completed successfully

🤖 Running AI Agent Tests...
==================================================
✅ Agent health check: healthy
✅ Knowledge base already populated
✅ All tests completed!

🔗 Running AI Integration Tests...
==================================================
✅ Integration test: Message processing successful
✅ Integration test: Memory retrieval successful
✅ Integration tests completed successfully

============================================================
📊 Test Results Summary
============================================================
1. Setup Tests: ✅ PASSED
2. Conversation Context Tests: ✅ PASSED
3. AI Agent Tests: ✅ PASSED
4. Integration Tests: ✅ PASSED

Overall: 4/4 test suites passed

🎉 All AI tests passed! The AI agent is working correctly.
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   ```bash
   # Install missing AI packages
   uv add langchain langchain-openai qdrant-client
   ```

2. **Environment Variables**:
   ```bash
   # Check if .env file exists and has required variables
   cat .env | grep -E "(OPENAI|QDRANT|MONGODB|LANGCHAIN)"
   ```

3. **Database Connection**:
   ```bash
   # Test MongoDB connection
   python -c "from app.db.client import database; import asyncio; asyncio.run(database.connect())"
   ```

4. **Knowledge Base Issues**:
   ```bash
   # Reinitialize knowledge base
   python tests/ai/setup/setup_ai_agent.py
   ```

### Debug Mode
```bash
# Run tests with debug output
python tests/ai/run_all_tests.py --debug

# Run individual test with verbose output
python tests/ai/test_ai_agent.py -v
```

## 📝 Adding New Tests

When adding new AI-related tests:

1. **Follow Naming Convention**:
   - Test files: `test_<feature>.py`
   - Setup files: `setup_<feature>.py`

2. **Update Test Runner**:
   - Add new test function to `run_all_tests.py`
   - Include in the main test sequence

3. **Documentation**:
   - Update this README with new test descriptions
   - Add usage examples

4. **Integration**:
   - Ensure new tests work with existing test suite
   - Update prerequisites if needed

## 🔄 Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run AI Tests
  run: |
    source .venv/bin/activate
    python tests/ai/run_all_tests.py
```

## 📞 Support

For issues with AI tests:
1. Check the troubleshooting section above
2. Review test output for specific error messages
3. Verify environment configuration
4. Check AI service logs for detailed error information
