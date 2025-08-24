#!/usr/bin/env python3
"""
Test script to verify the WhatsApp agent loop fix.
Run this to test the agent with a simple greeting.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.agents.whatsapp_agent.runner import run_agent
from app.core.logger import logger

async def test_greeting():
    """Test the agent with a simple greeting."""
    logger.info("🧪 [TEST] Starting agent loop fix test...")
    
    # Test with simple greeting
    test_conversation_id = "test_conv_123"
    test_message = "Hola"
    
    try:
        logger.info(f"🧪 [TEST] Testing with message: '{test_message}'")
        response = await run_agent(test_conversation_id, test_message)
        
        logger.info(f"🧪 [TEST] Agent response: '{response}'")
        logger.info("✅ [TEST] Test completed successfully!")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [TEST] Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test
    response = asyncio.run(test_greeting())
    print(f"\nFinal response: {response}")
