#!/usr/bin/env python3
"""
Test script for WhatsApp agent fixes.
Tests the improved agent with the question that was causing the infinite loop.
"""

import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.services.ai.agents.whatsapp_agent.runner import run_agent
from app.core.logger import logger


async def test_pricing_question():
    """Test the pricing question that was causing the infinite loop."""
    
    print("🧪 Testing WhatsApp Agent with pricing question...")
    print("=" * 60)
    
    # Test query that was causing the infinite loop
    test_query = "que precios tienen?"
    conversation_id = "test_conversation_001"
    
    try:
        print(f"🔍 Testing query: '{test_query}'")
        print(f"💬 Conversation ID: {conversation_id}")
        print("-" * 40)
        
        # Run the agent
        result = await run_agent(
            conversation_id=conversation_id,
            user_text=test_query
        )
        
        print("✅ Agent execution completed!")
        print(f"📝 Response: {result}")
        print("-" * 40)
        
        # Check if the response is meaningful and not a fallback
        if result and len(result) > 20:
            if "configurando mi base de conocimiento" in result.lower():
                print("⚠️  Agent provided fallback response (knowledge base not ready)")
                return "fallback"
            elif "precios" in result.lower() or "plan" in result.lower():
                print("🎉 Agent provided a relevant response about pricing!")
                return "success"
            else:
                print("✅ Agent provided a response, but may not be about pricing")
                return "partial"
        else:
            print("❌ Agent response is too short or empty")
            return "error"
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        return "error"


async def test_simple_greeting():
    """Test a simple greeting to ensure basic functionality."""
    
    print("\n🧪 Testing WhatsApp Agent with simple greeting...")
    print("=" * 60)
    
    test_query = "hola"
    conversation_id = "test_conversation_002"
    
    try:
        print(f"🔍 Testing query: '{test_query}'")
        print(f"💬 Conversation ID: {conversation_id}")
        print("-" * 40)
        
        # Run the agent
        result = await run_agent(
            conversation_id=conversation_id,
            user_text=test_query
        )
        
        print("✅ Agent execution completed!")
        print(f"📝 Response: {result}")
        print("-" * 40)
        
        # Check if greeting is handled correctly (should NOT use tools)
        if result and len(result) > 5:
            if "hola" in result.lower() and len(result) < 200:
                print("🎉 Agent handled greeting correctly (short, direct response)!")
                return "success"
            else:
                print("✅ Agent responded to greeting")
                return "partial"
        else:
            print("❌ Agent response is too short")
            return "error"
            
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        print(f"❌ Test failed: {str(e)}")
        return "error"


async def main():
    """Run all tests."""
    
    print("🚀 Starting WhatsApp Agent Fix Tests")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Simple greeting (should be fast, no tools)
    results["greeting"] = await test_simple_greeting()
    
    # Test 2: Pricing question (was causing infinite loop)
    results["pricing"] = await test_pricing_question()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status_emoji = {
            "success": "✅",
            "partial": "⚠️ ",
            "fallback": "🔄",
            "error": "❌"
        }.get(result, "❓")
        
        print(f"{status_emoji} {test_name.capitalize()} test: {result}")
    
    # Overall assessment
    success_count = sum(1 for r in results.values() if r == "success")
    total_tests = len(results)
    
    print("-" * 40)
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! WhatsApp agent is working correctly.")
    elif success_count > 0:
        print(f"⚠️  {success_count}/{total_tests} tests passed. Some improvements needed.")
    else:
        print("❌ NO TESTS PASSED. Agent needs more work.")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        sys.exit(1)
