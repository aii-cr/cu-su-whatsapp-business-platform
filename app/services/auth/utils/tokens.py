"""JWT token management utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logger import logger


class TokenData:
    """Token data structure for JWT tokens."""
    
    def __init__(self, user_id: str = None, email: str = None, scopes: List[str] = None):
        self.user_id = user_id
        self.email = email
        self.scopes = scopes or []


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Type of token ("access" or "refresh")
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        # The JWT library automatically validates the 'exp' claim
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        return None 