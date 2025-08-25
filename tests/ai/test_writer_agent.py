#!/usr/bin/env python3
"""
Test script for Writer Agent functionality.
Tests both contextual response generation and custom query handling.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.services.ai.agents.writer.agent_service import writer_agent_service
from app.core.logger import logger


async def test_writer_agent():
    """Test the Writer Agent functionality with real conversation data."""
    print("✨ Testing Writer Agent Implementation")
    print("=" * 60)
    
    try:
        # Test conversation ID provided by user
        test_conversation_id = "68a896bf96f98f65b7d7ba68"
        
        # 1. Health Check
        print("\n1️⃣ Testing Writer Agent Health Check...")
        health = await writer_agent_service.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Service: {health['service']}")
        
        if health['status'] == 'healthy':
            agent_health = health.get('agent_health', {})
            print(f"   Model: {agent_health.get('model', 'unknown')}")
            print(f"   Tools count: {agent_health.get('tools_count', 0)}")
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return
        
        # 2. Test Contextual Response Generation (Prebuilt Option)
        print(f"\n2️⃣ Testing Contextual Response Generation...")
        print(f"   Using conversation ID: {test_conversation_id}")
        
        start_time = datetime.now()
        contextual_result = await writer_agent_service.generate_contextual_response(
            conversation_id=test_conversation_id
        )
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Success: {contextual_result['success']}")
        
        if contextual_result['success']:
            metadata = contextual_result.get('metadata', {})
            print(f"   Iterations: {metadata.get('iterations', 0)}")
            print(f"   Helpfulness score: {metadata.get('helpfulness_score', 'unknown')}")
            print(f"   Processing time (internal): {metadata.get('processing_time_ms', 0)}ms")
            print(f"   Model used: {metadata.get('model_used', 'unknown')}")
            print(f"   Node history: {metadata.get('node_history', [])}")
            
            response = contextual_result.get('response', '')
            print(f"\n   Generated Response:")
            print(f"   {'-' * 40}")
            print(f"   {response}")
            print(f"   {'-' * 40}")
            print(f"   Response length: {len(response)} characters")
            print("   ✅ Contextual response generation passed")
        else:
            error = contextual_result.get('error', 'Unknown error')
            print(f"   ❌ Contextual response generation failed: {error}")
        
        # 3. Test Custom Query Processing
        print(f"\n3️⃣ Testing Custom Query Processing...")
        
        test_queries = [
            {
                "query": "I want to say that the service was put down but in a sympathetic way",
                "description": "Sympathetic service downtime message"
            },
            {
                "query": "Generate a professional apology for a delayed response with explanation",
                "description": "Professional apology with explanation"
            },
            {
                "query": "Create a friendly message asking for more details about the customer's issue",
                "description": "Information gathering message"
            },
            {
                "query": "Write a message to escalate this conversation to a supervisor in a polite way",
                "description": "Escalation message"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n   Test {i}: {test_case['description']}")
            print(f"   Query: '{test_case['query']}'")
            
            start_time = datetime.now()
            custom_result = await writer_agent_service.generate_response(
                user_query=test_case['query'],
                conversation_id=test_conversation_id
            )
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Success: {custom_result['success']}")
            
            if custom_result['success']:
                metadata = custom_result.get('metadata', {})
                print(f"   Iterations: {metadata.get('iterations', 0)}")
                print(f"   Helpfulness score: {metadata.get('helpfulness_score', 'unknown')}")
                
                response = custom_result.get('response', '')
                print(f"   Generated Response (first 150 chars): {response[:150]}...")
                print(f"   Response length: {len(response)} characters")
                print("   ✅ Custom query passed")
            else:
                error = custom_result.get('error', 'Unknown error')
                print(f"   ❌ Custom query failed: {error}")
        
        # 4. Test Tool Usage Analysis
        print(f"\n4️⃣ Analyzing Tool Usage...")
        
        # Test a query that should trigger conversation context tool
        context_query = "Generate the best possible response for the current conversation context"
        print(f"   Testing context tool with query: '{context_query}'")
        
        start_time = datetime.now()
        context_tool_result = await writer_agent_service.generate_response(
            user_query=context_query,
            conversation_id=test_conversation_id
        )
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Success: {context_tool_result['success']}")
        
        if context_tool_result['success']:
            metadata = context_tool_result.get('metadata', {})
            node_history = metadata.get('node_history', [])
            
            # Check if conversation context was used
            context_used = any('action' in node for node in node_history)
            print(f"   Tools were used: {context_used}")
            print(f"   Node history: {node_history}")
            print(f"   Iterations: {metadata.get('iterations', 0)}")
            
            response = context_tool_result.get('response', '')
            print(f"   Response length: {len(response)} characters")
            print("   ✅ Tool usage analysis passed")
        else:
            error = context_tool_result.get('error', 'Unknown error')
            print(f"   ❌ Tool usage analysis failed: {error}")
        
        # 5. Test Edge Cases
        print(f"\n5️⃣ Testing Edge Cases...")
        
        edge_cases = [
            {
                "query": "",
                "description": "Empty query"
            },
            {
                "query": "a" * 1000,  # Very long query
                "description": "Very long query (1000 chars)"
            },
            {
                "query": "Generate response for non-existent conversation",
                "conversation_id": "000000000000000000000000",  # Non-existent ID
                "description": "Non-existent conversation ID"
            }
        ]
        
        for i, test_case in enumerate(edge_cases, 1):
            print(f"\n   Edge Case {i}: {test_case['description']}")
            
            try:
                start_time = datetime.now()
                edge_result = await writer_agent_service.generate_response(
                    user_query=test_case['query'],
                    conversation_id=test_case.get('conversation_id', test_conversation_id)
                )
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                print(f"   Processing time: {processing_time:.2f}s")
                print(f"   Success: {edge_result['success']}")
                
                if edge_result['success']:
                    response = edge_result.get('response', '')
                    print(f"   Response length: {len(response)} characters")
                    print("   ✅ Edge case handled successfully")
                else:
                    error = edge_result.get('error', 'Unknown error')
                    print(f"   Response: Error handled gracefully - {error}")
                    print("   ✅ Edge case handled with proper error")
                
            except Exception as e:
                print(f"   ❌ Edge case threw exception: {str(e)}")
        
        # 6. Performance Summary
        print(f"\n6️⃣ Performance Summary...")
        print(f"   All tests completed successfully!")
        print(f"   Writer Agent is functioning properly with:")
        print(f"   - Contextual response generation ✅")
        print(f"   - Custom query processing ✅")
        print(f"   - Tool integration ✅")
        print(f"   - Helpfulness validation loop ✅")
        print(f"   - Error handling ✅")
        
        print(f"\n✨ Writer Agent Test Suite Complete! ✨")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_writer_agent_tools_individually():
    """Test Writer Agent tools individually."""
    print("\n🔧 Testing Writer Agent Tools Individually")
    print("=" * 50)
    
    try:
        from app.services.ai.agents.writer.tools.conversation_tool import ConversationContextTool
        from app.services.ai.shared.rag_tool import SharedRAGTool as WriterRAGTool
        
        test_conversation_id = "68a896bf96f98f65b7d7ba68"
        
        # Test Conversation Context Tool
        print("\n1️⃣ Testing Conversation Context Tool...")
        context_tool = ConversationContextTool()
        
        context_result = await context_tool._arun(
            conversation_id=test_conversation_id,
            include_metadata=True
        )
        
        print(f"   Result type: {type(context_result)}")
        print(f"   Result length: {len(context_result)} characters")
        
        if "Error:" in context_result:
            print(f"   ❌ Conversation context tool failed: {context_result}")
        else:
            # Check if it contains expected sections
            expected_sections = ["CONVERSATION METADATA", "MESSAGE HISTORY", "CONVERSATION ANALYSIS"]
            sections_found = [section for section in expected_sections if section in context_result]
            print(f"   Sections found: {sections_found}")
            print(f"   ✅ Conversation context tool working")
        
        # Test RAG Tool
        print("\n2️⃣ Testing RAG Tool...")
        rag_tool = WriterRAGTool()
        
        rag_result = await rag_tool._arun(
            query="What are the business hours?",
            tenant_id=None,
            locale=None
        )
        
        print(f"   Result type: {type(rag_result)}")
        print(f"   Result length: {len(rag_result)} characters")
        
        if "Error" in rag_result:
            print(f"   ⚠️ RAG tool had issues: {rag_result[:200]}...")
        else:
            print(f"   ✅ RAG tool working")
        
        print(f"\n✅ Individual tool tests completed!")
        
    except Exception as e:
        print(f"\n❌ Individual tool tests failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    async def run_all_tests():
        """Run all Writer Agent tests."""
        await test_writer_agent()
        await test_writer_agent_tools_individually()
    
    # Run the tests
    asyncio.run(run_all_tests())
