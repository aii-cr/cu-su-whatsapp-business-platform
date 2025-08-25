"""
LangSmith tracing setup for Writer Agent.
Based on the WhatsApp agent implementation.
"""

import os
from app.services.ai.config import ai_config
from app.core.logger import logger


def setup_tracing() -> None:
    """Configura variables de entorno para LangSmith (tracing v2)."""
    try:
        logger.info("🔍 [WRITER-TELEMETRY] Setting up LangSmith tracing...")
        
        if ai_config.langchain_tracing_v2:
            logger.info("🔍 [WRITER-TELEMETRY] LangSmith tracing enabled in config")
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            
            if ai_config.langchain_project:
                # Use writer-specific project name
                writer_project = f"{ai_config.langchain_project}-writer"
                os.environ["LANGCHAIN_PROJECT"] = writer_project
                logger.info(f"🔍 [WRITER-TELEMETRY] Project set: {writer_project}")
            else:
                logger.warning("⚠️ [WRITER-TELEMETRY] No LangChain project configured")
                
            if ai_config.langchain_api_key:
                os.environ["LANGCHAIN_API_KEY"] = ai_config.langchain_api_key
                logger.info("🔍 [WRITER-TELEMETRY] API key configured")
            else:
                logger.warning("⚠️ [WRITER-TELEMETRY] No LangChain API key configured")
                
            logger.info("✅ [WRITER-TELEMETRY] LangSmith tracing setup completed")
        else:
            logger.info("📋 [WRITER-TELEMETRY] LangSmith tracing disabled in config")
            
    except Exception as e:
        logger.error(f"❌ [WRITER-TELEMETRY] Failed to setup tracing: {str(e)}")
        # Don't raise - tracing failure shouldn't break agent execution
