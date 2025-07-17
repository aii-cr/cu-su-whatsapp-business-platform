# Database Fixes

This folder contains scripts to fix database schema issues that may arise during development or migration.

## Available Fixes

### 1. `fix_conversation_index.py`
**Issue**: Duplicate key error on `conversation_id` field in `conversations` collection
**Fix**: Removes the unique index on `conversation_id` field
**When to run**: When you get `E11000 duplicate key error collection: chat_platform.conversations index: conversation_id_1`

### 2. `fix_message_index.py`
**Issue**: Duplicate key error on `message_id` field in `messages` collection  
**Fix**: Removes the unique index on `message_id` field
**When to run**: When you get `E11000 duplicate key error collection: chat_platform.messages index: message_id_1`

## How to Run

From the project root, activate your virtual environment and run:

```bash
# Fix conversation index issue
python tests/db_fixes/fix_conversation_index.py

# Fix message index issue  
python tests/db_fixes/fix_message_index.py
```

## Notes

- These scripts are safe to run multiple times
- They will only remove indexes if they exist
- Always backup your database before running fixes in production
- These fixes are for development/testing environments where you don't need these unique constraints 