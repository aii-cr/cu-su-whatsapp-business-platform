#!/usr/bin/env python3
"""
Interactive RAG Testing
Allows manual testing of individual queries with detailed output.
"""

import asyncio
import time
from typing import List, Dict, Any

# LangChain imports
from langchain_core.documents import Document

# Local imports
from app.services.ai.rag.retriever import get_default_retriever

class InteractiveRAGTester:
    """Interactive RAG testing for manual query evaluation."""
    
    def __init__(self):
        self.retriever = None
        
    async def setup_retriever(self):
        """Set up the retriever for testing."""
        print("🔧 Setting up RAG retriever...")
        self.retriever = get_default_retriever(tenant_id=None, locale=None)
        print("✓ Retriever ready")
    
    async def test_single_query(self, query: str) -> Dict[str, Any]:
        """Test a single query and return detailed results."""
        if not self.retriever:
            await self.setup_retriever()
        
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Execute query
            results = await self.retriever.aget_relevant_documents(query)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Analyze results
            analysis = self._analyze_results(results)
            
            # Generate answer
            context = "\n".join([doc.page_content for doc in results[:3]]) if results else ""
            generated_answer = self._generate_answer_from_context(context, query)
            
            return {
                "query": query,
                "latency_ms": latency_ms,
                "results_count": len(results),
                "results": results,
                "analysis": analysis,
                "generated_answer": generated_answer,
                "context": context,
                "success": len(results) > 0
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "query": query,
                "latency_ms": 0,
                "results_count": 0,
                "error": str(e),
                "success": False
            }
    
    def _analyze_results(self, results: List[Document]) -> Dict[str, Any]:
        """Analyze retrieval results."""
        if not results:
            return {
                "relevance_score": 0.0,
                "content_quality": "none",
                "sections": [],
                "titles": []
            }
        
        # Analyze all results
        sections = []
        titles = []
        content_lengths = []
        
        for doc in results:
            metadata = doc.metadata
            content = doc.page_content
            
            sections.append(metadata.get("section", "Unknown"))
            titles.append(metadata.get("title", "No title"))
            content_lengths.append(len(content))
        
        # Calculate average content length
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        # Assess content quality
        if avg_content_length > 200:
            content_quality = "excellent"
        elif avg_content_length > 100:
            content_quality = "good"
        elif avg_content_length > 50:
            content_quality = "fair"
        else:
            content_quality = "poor"
        
        # Simple relevance score based on content length and result count
        relevance_score = min((avg_content_length / 200) * (len(results) / 5), 1.0)
        
        return {
            "relevance_score": relevance_score,
            "content_quality": content_quality,
            "sections": sections,
            "titles": titles,
            "avg_content_length": avg_content_length,
            "unique_sections": list(set(sections))
        }
    
    def _generate_answer_from_context(self, context: str, question: str) -> str:
        """Generate a simple answer from context."""
        if not context:
            return "No se encontró información relevante."
        
        # Simple answer generation based on question type
        question_lower = question.lower()
        
        if "precio" in question_lower or "costo" in question_lower or "cuánto" in question_lower:
            # Look for price information
            if "₡" in context:
                price_match = context.split("₡")[1].split()[0] if "₡" in context else "no especificado"
                return f"El precio es {price_match} colones."
        
        if "canales" in question_lower:
            if "88" in context:
                return "El servicio IPTV incluye 88 canales."
        
        if "whatsapp" in question_lower:
            if "+506 7087-8240" in context:
                return "El número de WhatsApp es +506 7087-8240."
        
        if "instalación" in question_lower or "tiempo" in question_lower:
            if "48" in context and "72" in context:
                return "La instalación se realiza entre 48 y 72 horas posteriores a la compra."
        
        # Default: return first sentence of context
        sentences = context.split('.')
        return sentences[0] + "." if sentences else context[:100] + "..."
    
    def print_detailed_results(self, result: Dict[str, Any]):
        """Print detailed results for a query."""
        print(f"\n📊 QUERY RESULTS")
        print("=" * 60)
        print(f"Query: {result['query']}")
        print(f"Latency: {result['latency_ms']:.2f}ms")
        print(f"Results found: {result['results_count']}")
        print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        
        # Analysis
        analysis = result["analysis"]
        print(f"\n📈 ANALYSIS:")
        print(f"  Relevance score: {analysis['relevance_score']:.3f}")
        print(f"  Content quality: {analysis['content_quality']}")
        print(f"  Average content length: {analysis['avg_content_length']:.0f} chars")
        print(f"  Unique sections: {len(analysis['unique_sections'])}")
        
        # Sections found
        if analysis['sections']:
            print(f"\n📂 SECTIONS FOUND:")
            for i, section in enumerate(analysis['sections'][:5], 1):
                print(f"  {i}. {section}")
        
        # Generated answer
        print(f"\n💬 GENERATED ANSWER:")
        print(f"  {result['generated_answer']}")
        
        # Top results preview
        if result['results']:
            print(f"\n📄 TOP RESULTS PREVIEW:")
            for i, doc in enumerate(result['results'][:3], 1):
                print(f"\n  --- Result {i} ---")
                print(f"  Section: {doc.metadata.get('section', 'Unknown')}")
                print(f"  Title: {doc.metadata.get('title', 'No title')}")
                print(f"  Content: {doc.page_content[:150]}...")
    
    async def run_interactive_session(self):
        """Run an interactive testing session."""
        print("🚀 Interactive RAG Testing Session")
        print("=" * 80)
        print("Enter queries to test the RAG system. Type 'quit' to exit.")
        print("Example queries:")
        print("  - ¿Cuál es el precio del plan de 500 Mbps?")
        print("  - ¿Cuántos canales tiene el IPTV?")
        print("  - ¿Cuál es el número de WhatsApp?")
        print("  - ¿Quién es ADN?")
        print("-" * 80)
        
        # Setup retriever
        await self.setup_retriever()
        
        while True:
            try:
                # Get query from user
                query = input("\n🔍 Enter your query (or 'quit' to exit): ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    print("⚠️  Please enter a valid query.")
                    continue
                
                # Test the query
                result = await self.test_single_query(query)
                
                # Print results
                self.print_detailed_results(result)
                
            except KeyboardInterrupt:
                print("\n👋 Session interrupted. Goodbye!")
                break
            except EOFError:
                print("\n👋 Session ended. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")

async def main():
    """Run the interactive RAG test."""
    tester = InteractiveRAGTester()
    await tester.run_interactive_session()

if __name__ == "__main__":
    asyncio.run(main())
