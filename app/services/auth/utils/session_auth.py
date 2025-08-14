"""Session authentication utilities for cookie-based authentication."""

import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Response, Depends, Request
from pydantic import BaseModel
from bson import ObjectId

from app.core.config import settings
from app.core.logger import logger
from app.config.error_codes import ErrorCode, get_error_response

# In-memory storage for invalidated session tokens (in production, use Redis)
_invalidated_sessions: set = set()

class SessionData(BaseModel):
    """Session data model."""
    user_id: str
    email: str
    exp: datetime
    type: str
    iat: datetime
    last_activity: str

def create_session_token(user_data: Dict[str, Any]) -> str:
    """
    Create a session token for the user.
    
    Args:
        user_data: User data to encode in token
        
    Returns:
        JWT session token
    """
    try:
        # Set expiration time
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)
        
        # Prepare token payload
        to_encode = {
            "sub": str(user_data["_id"]),
            "email": user_data["email"],
        }
        
        # Add session-specific fields
        to_encode.update({
            "exp": expire,
            "type": "session",
            "iat": datetime.now(timezone.utc),  # Issued at time for inactivity tracking
            "last_activity": datetime.now(timezone.utc).isoformat()  # Last activity timestamp
        })
        
        # Create JWT token
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        logger.info(f"Session token created for user {user_data['email']}")
        return token
        
    except Exception as e:
        logger.error(f"Failed to create session token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)["message"],
        )

def verify_session_token(token: str) -> Optional[SessionData]:
    """
    Verify and decode session token.
    
    Args:
        token: JWT session token
        
    Returns:
        SessionData if valid, None if invalid
    """
    try:
        # Check if token is in invalidated sessions
        if token in _invalidated_sessions:
            logger.warning("Attempted to use invalidated session token")
            return None
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != "session":
            logger.warning(f"Invalid token type: {token_type}")
            return None
        
        # Check if token is expired
        exp = payload.get("exp")
        if not exp:
            logger.warning("Token missing expiration")
            return None
        
        # Convert exp to datetime if it's a timestamp
        if isinstance(exp, (int, float)):
            exp = datetime.fromtimestamp(exp, tz=timezone.utc)
        
        if exp < datetime.now(timezone.utc):
            logger.warning("Session token expired")
            return None
        
        # Check inactivity timeout
        last_activity_str = payload.get("last_activity")
        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                inactivity_timeout = datetime.now(timezone.utc) - timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES)
                if last_activity < inactivity_timeout:
                    logger.warning(f"Session expired due to inactivity. Last activity: {last_activity}")
                    return None
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid last_activity timestamp: {e}")
                return None
        
        # Create session data
        session_data = SessionData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            exp=exp,
            type=token_type,
            iat=datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc),
            last_activity=last_activity_str or datetime.now(timezone.utc).isoformat()
        )
        
        return session_data
        
    except jwt.ExpiredSignatureError:
        logger.warning("Session token expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Invalid session token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Session token verification failed: {str(e)}")
        return None

def update_session_activity(token: str) -> Optional[str]:
    """
    Update the last_activity timestamp in a session token.
    
    Args:
        token: Current session token
        
    Returns:
        Updated session token or None if invalid
    """
    try:
        # Verify current token
        session_data = verify_session_token(token)
        if not session_data:
            return None
        
        # Create new token with updated activity
        to_encode = {
            "sub": session_data.user_id,
            "email": session_data.email,
            "exp": session_data.exp,
            "type": session_data.type,
            "iat": session_data.iat,
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        # Create new JWT token
        new_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return new_token
        
    except Exception as e:
        logger.error(f"Failed to update session activity: {str(e)}")
        return None

def invalidate_session_token(token: str) -> None:
    """
    Invalidate a session token to prevent reuse.
    
    Args:
        token: Session token to invalidate
    """
    try:
        # Add token to invalidated sessions set
        _invalidated_sessions.add(token)
        
        # Clean up old invalidated tokens (keep only last 1000)
        if len(_invalidated_sessions) > 1000:
            # Remove oldest tokens (simple cleanup)
            _invalidated_sessions.clear()
        
        logger.info("Session token invalidated")
        
    except Exception as e:
        logger.error(f"Failed to invalidate session token: {str(e)}")

async def get_current_session_token(request: Request) -> SessionData:
    """
    Get current session token from request cookies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        SessionData from token
        
    Raises:
        HTTPException: If no valid session token found
    """
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        logger.warning("No session token found in cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_MISSING)["message"],
        )
    
    session_data = verify_session_token(session_token)
    
    if not session_data:
        logger.warning("Invalid session token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_EXPIRED)["message"],
        )
    
    return session_data

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
    Get the current active user (alias for get_current_user).
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