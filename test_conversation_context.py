#!/usr/bin/env python3
"""
Test script for conversation context functionality.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_conversation_context():
    """Test the conversation context functionality."""
    
    print("🧪 Testing Conversation Context Functionality...")
    
    try:
        # Test memory service import
        from app.services.ai.memory_service import memory_service
        print("✅ Memory service imported successfully")
        
        # Test agent service import
        from app.services.ai.agent_service import agent_service
        print("✅ Agent service imported successfully")
        
        # Test conversation context creation
        test_conversation_id = "test_conversation_123"
        
        # Test memory service methods
        memory = memory_service.get_conversation_memory(test_conversation_id)
        print("✅ Conversation memory created successfully")
        
        # Test session data
        memory_service.update_session_data(test_conversation_id, {
            "language": "es",
            "intent": "faq",
            "confidence": 0.8
        })
        print("✅ Session data updated successfully")
        
        # Test conversation summary
        test_history = [
            {"role": "user", "content": "Hola, necesito información sobre precios"},
            {"role": "assistant", "content": "Te ayudo con información sobre nuestros precios..."},
            {"role": "user", "content": "¿Cuánto cuesta el plan básico?"}
        ]
        
        summary = memory_service.create_conversation_summary(test_history)
        print(f"✅ Conversation summary created: {summary}")
        
        # Test conversation context
        context = memory_service.get_conversation_context(test_conversation_id)
        print(f"✅ Conversation context retrieved: {context['memory_size']} messages")
        
        # Test memory statistics
        stats = memory_service.get_memory_stats()
        print(f"✅ Memory statistics: {stats['active_conversations']} active conversations")
        
        # Test memory clearing
        memory_service.clear_conversation_memory(test_conversation_id)
        print("✅ Conversation memory cleared successfully")
        
        print("\n🎉 All conversation context tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_agent_with_context():
    """Test the agent with conversation context."""
    
    print("\n🧪 Testing Agent with Conversation Context...")
    
    try:
        from app.services.ai.agent_service import agent_service
        
        # Test agent health check
        health = await agent_service.health_check()
        print(f"✅ Agent health check: {health['status']}")
        
        # Test memory statistics in health check
        if 'memory_service' in health:
            print(f"✅ Memory service stats in health check: {health['memory_service']['active_conversations']} conversations")
        
        print("🎉 Agent context tests passed!")
        
    except Exception as e:
        print(f"❌ Agent test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Run all tests."""
    print("🚀 Starting Conversation Context Tests...\n")
    
    # Test conversation context
    context_success = await test_conversation_context()
    
    # Test agent with context
    agent_success = await test_agent_with_context()
    
    if context_success and agent_success:
        print("\n🎉 All tests passed! Conversation context is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

