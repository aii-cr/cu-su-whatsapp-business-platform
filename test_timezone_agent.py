#!/usr/bin/env python3
"""
Test script to verify the timezone-aware agent greetings.
Run this to test the agent with greetings and see time-contextual responses.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.agents.whatsapp_agent.runner import run_agent
from app.services.ai.agents.whatsapp_agent.timezone_utils import get_contextual_time_info, get_costa_rica_time
from app.core.logger import logger

async def test_time_aware_greetings():
    """Test the agent with time-aware greetings."""
    logger.info("🧪 [TEST] Starting timezone-aware agent test...")
    
    # Show current Costa Rica time
    cr_time = get_costa_rica_time()
    time_context_es = get_contextual_time_info("es")
    time_context_en = get_contextual_time_info("en")
    
    print(f"\n📅 Costa Rica Time: {cr_time.strftime('%H:%M %Z on %A, %B %d, %Y')}")
    print(f"🇪🇸 Spanish context: {time_context_es}")
    print(f"🇺🇸 English context: {time_context_en}")
    print("="*80)
    
    # Test with different greetings
    test_cases = [
        ("hola", "Spanish greeting"),
        ("buenas", "Spanish casual greeting"),
        ("hello", "English greeting"),
        ("buenos días", "Spanish morning greeting (should be corrected to current time)"),
    ]
    
    for message, description in test_cases:
        test_conversation_id = f"test_conv_{message.replace(' ', '_')}"
        
        try:
            print(f"\n🧪 [TEST] Testing {description}: '{message}'")
            response = await run_agent(test_conversation_id, message)
            
            print(f"🤖 [RESPONSE] {response}")
            print("-" * 60)
            
        except Exception as e:
            logger.error(f"❌ [TEST] Test failed for '{message}': {str(e)}")
            print(f"❌ Error: {str(e)}")
            print("-" * 60)
        
        # Small delay between tests
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_time_aware_greetings())
