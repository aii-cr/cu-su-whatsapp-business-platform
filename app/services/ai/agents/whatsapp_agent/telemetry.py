# NEW CODE
"""
Inicializa LangSmith tracing (tracing v2) desde la configuración.
"""

import os
from app.services.ai.config import ai_config
from app.core.logger import logger


def setup_tracing() -> None:
    """Configura variables de entorno para LangSmith (tracing v2)."""
    try:
        logger.info("🔍 [TELEMETRY] Setting up LangSmith tracing...")
        
        if ai_config.langchain_tracing_v2:
            logger.info("🔍 [TELEMETRY] LangSmith tracing enabled in config")
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            
            if ai_config.langchain_project:
                os.environ["LANGCHAIN_PROJECT"] = ai_config.langchain_project
                logger.info(f"🔍 [TELEMETRY] Project set: {ai_config.langchain_project}")
            else:
                logger.warning("⚠️ [TELEMETRY] No LangChain project configured")
                
            if ai_config.langchain_api_key:
                os.environ["LANGCHAIN_API_KEY"] = ai_config.langchain_api_key
                logger.info("🔍 [TELEMETRY] API key configured")
            else:
                logger.warning("⚠️ [TELEMETRY] No LangChain API key configured")
                
            logger.info("✅ [TELEMETRY] LangSmith tracing setup completed")
        else:
            logger.info("📋 [TELEMETRY] LangSmith tracing disabled in config")
            
    except Exception as e:
        logger.error(f"❌ [TELEMETRY] Failed to setup tracing: {str(e)}")
        # Don't raise - tracing failure shouldn't break agent execution
