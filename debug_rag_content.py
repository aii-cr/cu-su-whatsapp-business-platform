#!/usr/bin/env python3
"""
Debug script to check what documents are being retrieved by the RAG system.
"""

import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.services.ai.shared.tools.rag.retriever import retrieve_information
from app.services.ai.agents.whatsapp_agent.tools import sync_retrieve_information
from app.core.logger import logger


async def debug_rag_retrieval():
    """Debug RAG retrieval to see what content is being returned."""
    
    print("🔍 DEBUG: RAG Content Retrieval")
    print("=" * 60)
    
    queries = [
        "precios planes internet",
        "planes residenciales precios",
        "que precios tienen",
        "planes internet todos"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🧪 TEST {i}: Query = '{query}'")
        print("-" * 40)
        
        try:
            # Test async version (used by Writer agent)
            print("📋 ASYNC VERSION (Writer Agent):")
            async_result = await retrieve_information(query)
            print(f"Length: {len(async_result)} chars")
            print(f"Content preview: {async_result[:200]}...")
            
            if "NO_CONTEXT_AVAILABLE" in async_result:
                print("❌ NO CONTEXT AVAILABLE")
            else:
                # Count how many plans are mentioned
                plan_indicators = ["100/100", "250/250", "500/500", "1/1 Gbps", "₡20,500", "₡26,600", "₡33,410", "₡49,500"]
                found_plans = [indicator for indicator in plan_indicators if indicator in async_result]
                print(f"📊 Plans found: {len(found_plans)} indicators -> {found_plans}")
            
            print("\n📋 SYNC VERSION (WhatsApp Agent):")
            sync_result = sync_retrieve_information.invoke({"query": query})
            print(f"Length: {len(sync_result)} chars")
            print(f"Content preview: {sync_result[:200]}...")
            
            if "NO_CONTEXT_AVAILABLE" in sync_result:
                print("❌ NO CONTEXT AVAILABLE")
            else:
                # Count how many plans are mentioned
                plan_indicators = ["100/100", "250/250", "500/500", "1/1 Gbps", "₡20,500", "₡26,600", "₡33,410", "₡49,500"]
                found_plans = [indicator for indicator in plan_indicators if indicator in sync_result]
                print(f"📊 Plans found: {len(found_plans)} indicators -> {found_plans}")
            
            # Compare results
            if async_result == sync_result:
                print("✅ RESULTS MATCH")
            else:
                print("❌ RESULTS DIFFER!")
                print(f"Async length: {len(async_result)}, Sync length: {len(sync_result)}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("This debug helps identify if the issue is:")
    print("1. RAG retrieval not finding the right documents")
    print("2. Difference between async and sync versions")
    print("3. Knowledge base missing complete plan information")


if __name__ == "__main__":
    try:
        asyncio.run(debug_rag_retrieval())
    except KeyboardInterrupt:
        print("\n⚠️ Debug interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug failed: {str(e)}")
        sys.exit(1)
