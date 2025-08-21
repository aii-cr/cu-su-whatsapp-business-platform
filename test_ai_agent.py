#!/usr/bin/env python3
"""
Test script for AI Agent functionality.
Run this script to test the AI agent components.
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ai.agent_service import agent_service
from app.services.ai.rag.ingest import check_collection_health, ingest_documents
from app.core.logger import logger


async def test_ai_agent():
    """Test the AI agent functionality."""
    print("🤖 Testing AI Agent Implementation")
    print("=" * 50)
    
    try:
        # 1. Health Check
        print("\n1️⃣ Testing Agent Health Check...")
        health = await agent_service.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Initialized: {health['initialized']}")
        
        # 2. Collection Health
        print("\n2️⃣ Testing Knowledge Base Health...")
        collection_health = await check_collection_health()
        print(f"   Collection exists: {collection_health.get('collection_exists', False)}")
        print(f"   Vectors count: {collection_health.get('vectors_count', 0)}")
        
        # 3. Ingestion (if needed)
        if not collection_health.get('collection_exists', False) or collection_health.get('vectors_count', 0) == 0:
            print("\n3️⃣ Running Knowledge Base Ingestion...")
            ingestion_result = await ingest_documents()
            print(f"   Success: {ingestion_result.success}")
            print(f"   Documents processed: {ingestion_result.documents_processed}")
            print(f"   Chunks stored: {ingestion_result.chunks_stored}")
        else:
            print("\n3️⃣ Knowledge Base already populated ✅")
        
        # 4. Test Message Processing
        print("\n4️⃣ Testing Message Processing...")
        test_messages = [
            "Hola, ¿cuáles son sus precios?",
            "Hi, what are your business hours?",
            "¿Puedo hacer una reserva?",
            "How do I make a payment?"
        ]
        
        from bson import ObjectId
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   Test {i}: '{message}'")
            # Create valid ObjectIds for test
            test_conversation_id = str(ObjectId())
            test_message_id = str(ObjectId())
            
            result = await agent_service.process_whatsapp_message(
                conversation_id=test_conversation_id,
                message_id=test_message_id,
                user_text=message,
                customer_phone="+50684716592",
                ai_autoreply_enabled=True,
                is_first_message=(i == 1)
            )
            
            print(f"   Success: {result['success']}")
            if result['success'] and result['ai_response_sent']:
                print(f"   Response: {result['response_text'][:100]}...")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Requires handoff: {result.get('requires_human_handoff', False)}")
            
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_ai_agent())
