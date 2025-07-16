from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes.whatsapp import router as whatsapp_router
from app.db.chat_platform_db import mongo
from app.services.database_service import initialize_database
from app.core.logger import logger


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Using a context manager for lifecycle events:
    1. Code before "yield" acts like "startup".
    2. Code after "yield" acts like "shutdown".
    """
    logger.info("WhatsApp Business API Backend is starting up...")
    
    await mongo.connect()
    # Initialize database collections and indexes
    await initialize_database()
    
    yield
    
    # Shutdown logic here
    await mongo.disconnect()
    logger.info("WhatsApp Business API Backend is shutting down...")


def create_app() -> FastAPI:
    """
    Application factory that creates and configures the FastAPI instance,
    attaching the new lifespan context.
    """
    app = FastAPI(
        title="WhatsApp Business API Backend",
        version="1.0.0",
        lifespan=app_lifespan  
    )

    # Include the WhatsApp routes
    app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])

    return app
    

app = create_app()
