#!/usr/bin/env python3
"""
Comprehensive test runner for all AI agent tests.
Run this script to execute all AI-related tests in the correct order.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def run_setup_tests():
    """Run setup and initialization tests."""
    print("🔧 Running AI Agent Setup Tests...")
    print("=" * 50)
    
    try:
        # Import and run setup
        from tests.ai.setup.setup_ai_agent import main as setup_main
        await setup_main()
        print("✅ Setup tests completed successfully")
        return True
    except Exception as e:
        print(f"❌ Setup tests failed: {str(e)}")
        return False

async def run_conversation_context_tests():
    """Run conversation context tests."""
    print("\n🧠 Running Conversation Context Tests...")
    print("=" * 50)
    
    try:
        # Import and run conversation context tests
        from tests.ai.test_conversation_context import main as context_main
        result = await context_main()
        if result == 0:
            print("✅ Conversation context tests completed successfully")
            return True
        else:
            print("❌ Conversation context tests failed")
            return False
    except Exception as e:
        print(f"❌ Conversation context tests failed: {str(e)}")
        return False

async def run_ai_agent_tests():
    """Run AI agent functionality tests."""
    print("\n🤖 Running AI Agent Tests...")
    print("=" * 50)
    
    try:
        # Import and run AI agent tests
        from tests.ai.test_ai_agent import test_ai_agent
        await test_ai_agent()
        print("✅ AI agent tests completed successfully")
        return True
    except Exception as e:
        print(f"❌ AI agent tests failed: {str(e)}")
        return False

async def run_integration_tests():
    """Run integration tests for the complete AI system."""
    print("\n🔗 Running AI Integration Tests...")
    print("=" * 50)
    
    try:
        from app.services.ai.agents.whatsapp.agent_service import agent_service
        from app.services.ai.shared.memory_service import memory_service
        
        # Test complete flow
        print("Testing complete AI conversation flow...")
        
        # Create test conversation
        test_conversation_id = "integration_test_123"
        test_message_id = "msg_123"
        
        # Test message processing
        result = await agent_service.process_whatsapp_message(
            conversation_id=test_conversation_id,
            message_id=test_message_id,
            user_text="Hola, necesito información sobre precios",
            customer_phone="+50684716592",
            ai_autoreply_enabled=True,
            is_first_message=True
        )
        
        if result['success']:
            print("✅ Integration test: Message processing successful")
            
            # Test memory retrieval
            context = await agent_service.get_conversation_context(test_conversation_id)
            if context and 'conversation_id' in context:
                print("✅ Integration test: Memory retrieval successful")
            else:
                print("❌ Integration test: Memory retrieval failed")
                return False
        else:
            print("❌ Integration test: Message processing failed")
            return False
        
        print("✅ Integration tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {str(e)}")
        return False

async def main():
    """Run all AI tests in the correct order."""
    print("🚀 Starting Comprehensive AI Agent Tests...")
    print("=" * 60)
    
    results = []
    
    # 1. Setup tests
    results.append(await run_setup_tests())
    
    # 2. Conversation context tests
    results.append(await run_conversation_context_tests())
    
    # 3. AI agent tests
    results.append(await run_ai_agent_tests())
    
    # 4. Integration tests
    results.append(await run_integration_tests())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    test_names = [
        "Setup Tests",
        "Conversation Context Tests", 
        "AI Agent Tests",
        "Integration Tests"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i+1}. {name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} test suites passed")
    
    if passed == len(results):
        print("\n🎉 All AI tests passed! The AI agent is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} test suite(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
