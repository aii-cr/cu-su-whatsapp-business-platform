"""Session-based authentication utilities using cookies."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import APIKeyCookie
from bson import ObjectId
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logger import logger
from app.config.error_codes import ErrorCode, get_error_response

# Cookie-based security scheme
session_cookie = APIKeyCookie(
    name="session_token",
    scheme_name="CookieAuth",
    description=(
        "Cookie-based auth. endpoint upon successful login and must be present on subsequent requests."
    ),
    auto_error=True
)


class SessionData:
    """Session data structure for cookie-based sessions."""
    
    def __init__(self, user_id: str = None, email: str = None, scopes: list = None):
        self.user_id = user_id
        self.email = email
        self.scopes = scopes or []


def create_session_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a session token for cookies.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded session token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.SESSION_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "session"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a session token.
    
    Args:
        token: Session token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        # The JWT library automatically validates the 'exp' claim
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != "session":
            logger.warning(f"Token type mismatch: expected session, got {payload.get('type')}")
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning(f"Session token verification failed: {str(e)}")
        return None


async def get_current_session_token(
    session_token: str = Depends(session_cookie)
) -> SessionData:
    """
    Extract and validate the current user from session token.
    
    Args:
        session_token: Session token from cookie
        
    Returns:
        SessionData object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = verify_session_token(session_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_EXPIRED)["message"],
            )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        scopes: list[str] = payload.get("scopes", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
            )
            
        return SessionData(user_id=user_id, email=email, scopes=scopes)
        
    except JWTError as e:
        logger.error(f"Session token validation failed: {str(e)}")
        # Check if it's an expiration error
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_EXPIRED)["message"],
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
            )
    except Exception as e:
        logger.error(f"Session token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
        )


async def get_current_user(session_data: SessionData = Depends(get_current_session_token)):
    """
    Get the current authenticated user from the database.
    
    Args:
        session_data: Session data from cookie
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If user not found or inactive
    """
    from app.db.client import database
    from app.db.models.auth.user import User, UserStatus
    
    try:
        user_id = ObjectId(session_data.user_id)
        user_doc = await database.db.users.find_one({"_id": user_id})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_USER_NOT_FOUND)["message"],
            )
        
        user = User(**user_doc)
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_USER_INACTIVE)["message"],
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
        )


async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get the current active user (alias for get_current_user for clarity).
    
    Args:
        current_user: Current user from dependency
        
    Returns:
        Active user object
    """
    return current_user


def set_session_cookie(response: Response, session_token: str, max_age: int = None):
    """
    Set session cookie in response.
    
    Args:
        response: FastAPI response object
        session_token: Session token to set
        max_age: Cookie max age in seconds (defaults to session timeout)
    """
    if max_age is None:
        max_age = settings.SESSION_EXPIRE_MINUTES * 60
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",  # HTTPS only in production
        samesite="lax",
        path="/"
    )


def clear_session_cookie(response: Response):
    """
    Clear session cookie in response.
    
    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key="session_token",
        path="/"
    ) 