#!/usr/bin/env python3
"""
Setup script for AI Agent.
Installs dependencies and initializes the knowledge base.
"""

import asyncio
import subprocess
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

def activate_venv():
    """Activate the virtual environment if it exists."""
    venv_path = os.path.join(os.path.dirname(__file__), '.venv')
    if os.path.exists(venv_path):
        # Add the virtual environment's site-packages to Python path
        site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
            print("✅ Virtual environment activated")
            return True
        else:
            print("⚠️  Virtual environment found but site-packages not accessible")
            return False
    else:
        print("⚠️  No virtual environment found at .venv")
        return False

def check_dependencies():
    """Check if AI agent dependencies are available."""
    print("📦 Checking AI Agent dependencies...")
    try:
        # Try to import key AI dependencies
        import langchain
        import qdrant_client
        import openai
        print("✅ AI dependencies are available!")
        return True
    except ImportError as e:
        print(f"❌ Missing AI dependencies: {e}")
        print("Please run: uv add <missing-package>")
        return False

async def initialize_knowledge_base():
    """Initialize the knowledge base."""
    print("🧠 Initializing knowledge base...")
    
    try:
        from app.services.ai.shared.tools.rag.ingest import ingest_documents
        
        result = await ingest_documents()
        
        if result.success:
            print(f"✅ Knowledge base initialized successfully!")
            print(f"   Documents processed: {result.documents_processed}")
            print(f"   Chunks created: {result.chunks_created}")
            print(f"   Chunks stored: {result.chunks_stored}")
            print(f"   Processing time: {result.processing_time_ms}ms")
            return True
        else:
            print(f"❌ Knowledge base initialization failed:")
            for error in result.errors:
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing knowledge base: {str(e)}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    print("🔧 Checking environment configuration...")
    
    try:
        from app.core.config import settings
        
        # Check if required settings are available
        required_settings = {
            'OPENAI_API_KEY': settings.OPENAI_API_KEY,
            'QDRANT_URL': settings.QDRANT_URL,
            'QDRANT_API_KEY': settings.QDRANT_API_KEY,
            'MONGODB_URI': settings.MONGODB_URI
        }
        
        missing_vars = []
        for var_name, var_value in required_settings.items():
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease add these to your .env file:")
            print("OPENAI_API_KEY=your_openai_api_key")
            print("QDRANT_URL=your_qdrant_url")
            print("QDRANT_API_KEY=your_qdrant_api_key")
            print("MONGODB_URI=your_mongodb_uri")
            return False
        
        print("✅ Environment configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {str(e)}")
        print("Make sure your .env file exists and contains the required variables.")
        return False

async def main():
    """Main setup function."""
    print("🤖 AI Agent Setup")
    print("=" * 30)
    
    # Activate virtual environment
    activate_venv()
    
    # Check environment
    if not check_environment():
        print("\n❌ Setup failed: Missing environment configuration")
        return
    
    # Check AI dependencies
    if not check_dependencies():
        print("\n❌ Setup failed: Missing AI dependencies")
        return
    
    # Initialize knowledge base
    if not await initialize_knowledge_base():
        print("\n❌ Setup failed: Could not initialize knowledge base")
        return
    
    print("\n🎉 AI Agent setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your FastAPI server: uvicorn app.main:app --reload")
    print("2. Test the AI agent: python test_ai_agent.py")
    print("3. Check the API documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(main())
