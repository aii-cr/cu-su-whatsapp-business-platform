from fastapi import FastAPI
from app.db.mongo import MongoDBClient
from app.api.routes.auth_routes import router as auth_router

app = FastAPI()

# Events
@app.on_event("startup")
async def startup_event():
    MongoDBClient.get_client()

@app.on_event("shutdown")
async def shutdown_event():
    MongoDBClient.close_client()

# Routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return {"message": "Heimdal is here!"}