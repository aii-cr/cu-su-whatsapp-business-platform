from fastapi import APIRouter, HTTPException
from app.core.logger import logger
from app.db.chat_platform_db import mongo

router = APIRouter()

@router.get("/test-db")
async def test_db():
    try:
        collections = await mongo.db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed") 