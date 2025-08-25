# Testing Guide

This directory contains tests for the WhatsApp Business Platform backend.

## Running Tests

### Prerequisites
1. Ensure your virtual environment is activated
2. Make sure your backend server is running
3. Ensure MongoDB is running and accessible

### Test User Setup
Before running tests, you need to create a test user in your database:

```bash
# Run the test user insertion script
python tests/db_users/insert_test_user.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_whatsapp_send.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app

# Stop on first failure
pytest --maxfail=1

# Run AI tests specifically
python tests/ai/run_all_tests.py
python tests/ai/test_ai_agent.py
python tests/ai/test_conversation_context.py
```

## Test Structure

### Core Tests
- `test_main.py` - Basic API health checks
- `test_whatsapp_send.py` - WhatsApp message sending functionality
- `test_auth_services.py` - Authentication and authorization tests
- `test_session_management.py` - Session management and security tests

### Feature Tests
- `conversations/` - Conversation management tests
- `audit/` - Audit logging tests
- `ai/` - AI agent tests and setup scripts

### Database Utilities
- `db_fixes/` - Database schema fix scripts
- `db_users/` - User management utilities

## Environment Variables

Make sure your `.env` file contains the necessary test configuration:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=chat_platform
# ... other required variables
```

## Troubleshooting

### Import Errors
If you get `ModuleNotFoundError: No module named 'app'`, run tests with:
```bash
PYTHONPATH=. pytest
```

### Database Connection Issues
- Ensure MongoDB is running
- Check your `MONGODB_URI` and `DATABASE_NAME` settings
- Run database fixes if needed

### Test User Issues
- Ensure the test user exists in your database
- Check that the test user has the correct permissions
- Re-run the test user insertion script if needed 