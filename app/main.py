"""
Main entry point for the FastAPI WhatsApp integration app.
Initializes the application, includes routers, and configures logging
using the new lifespan context approach.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.routes.whatsapp import router as whatsapp_router
from app.core.logger import logger


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    Using a context manager for lifecycle events:
    1. Code before "yield" acts like "startup".
    2. Code after "yield" acts like "shutdown".
    """
    # Startup logic here
    logger.info("WhatsApp Business API Backend is starting up...")
    
    yield  # ---- The point at which FastAPI runs your application ----
    
    # Shutdown logic here
    logger.info("WhatsApp Business API Backend is shutting down...")


def create_app() -> FastAPI:
    """
    Application factory that creates and configures the FastAPI instance,
    attaching the new lifespan context.
    """
    app = FastAPI(
        title="WhatsApp Business API Backend",
        version="1.0.0",
        lifespan=app_lifespan  # Use the custom lifespan context
    )

    # Include the WhatsApp routes
    app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])

    return app


app = create_app()
