#!/usr/bin/env python3
"""
Test script to verify Writer Agent responds in English only.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.ai.agents.writer.agent_service import writer_agent_service


async def test_writer_english():
    """Test the Writer Agent to ensure it responds in English only."""
    
    print("🧪 Testing Writer Agent - English Only")
    print("=" * 40)
    
    # Test cases that might trigger Spanish responses
    test_cases = [
        {
            "name": "Simple greeting request",
            "query": "make a greeting"
        },
        {
            "name": "Spanish context request", 
            "query": "Help me respond to a customer who said 'Hola, necesito información sobre planes'"
        },
        {
            "name": "Service inquiry",
            "query": "Customer is asking about internet plans in Spanish, help me respond"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print("-" * 40)
        
        try:
            # Generate response
            result = await writer_agent_service.generate_response(
                user_query=test_case['query'],
                conversation_id=None,
                mode="custom"
            )
            
            if result.success:
                print("✅ Success!")
                
                if result.structured_response:
                    customer_response = result.structured_response.customer_response
                    reason = result.structured_response.reason
                    
                    print(f"📤 Customer Response: {customer_response}")
                    print(f"💭 Reasoning: {reason}")
                    
                    # Check if response contains Spanish
                    spanish_indicators = ["¡", "¿", "á", "é", "í", "ó", "ú", "ñ", "ü", "hola", "gracias", "por favor"]
                    has_spanish = any(indicator in customer_response.lower() for indicator in spanish_indicators)
                    
                    if has_spanish:
                        print("❌ WARNING: Response still contains Spanish content!")
                    else:
                        print("✅ GOOD: Response is in English only")
                        
                else:
                    print(f"📤 Raw Response: {result.raw_response}")
                
                print(f"⏱️  Processing time: {result.metadata.get('processing_time_ms', 0)}ms")
                print(f"🔄 Iterations: {result.metadata.get('iterations', 0)}")
                
            else:
                print(f"❌ Failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print()
    
    print("🎉 English-only testing completed!")


if __name__ == "__main__":
    asyncio.run(test_writer_english())
