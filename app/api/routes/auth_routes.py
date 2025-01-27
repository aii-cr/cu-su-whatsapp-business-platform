from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
from jose import jwt, JWTError

from app.schemas.auth_schema import RegisterSchema, LoginSchema
from app.db.chat_platform_db import MongoDBClient
from app.core.security import hash_password, verify_password, create_access_token
from app.config import settings
from app.core.utils import send_password_recovery_email

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register")
async def register_user(data: RegisterSchema):
    client = MongoDBClient().get_client()
    db = client[settings.DATABASE_NAME]
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = hash_password(data.password)
    user = {
        "username": data.email, 
        "email": data.email, 
        "hashed_password": hashed_password, 
        "role": data.role, 
        "full_name": data.full_name, 
        "phone": data.phone, 
        "mobile": data.mobile, 
        "is_active": True, 
        "created_at": datetime.utcnow()
    }
    await db.users.insert_one(user)
    return {"message": "Username already in use"}

@router.post("/login")
async def login_user(data: LoginSchema):
    client = MongoDBClient().get_client()
    db = client[settings.DATABASE_NAME]
    user = await db.users.find_one({"email": data.username})
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid Authentication")

    access_token = create_access_token({"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/recover-password")
async def recover_password(email: str):
    client = MongoDBClient().get_client()
    db = client[settings.DATABASE_NAME]
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = create_access_token({"sub": email}, timedelta(minutes=15))
    await send_password_recovery_email(email, token)
    return {"message": "Recovery mail sent"}

@router.get("/validate-token")
async def validate_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
