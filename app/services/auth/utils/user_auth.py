from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from .tokens import verify_token, TokenData

# Bearer token security scheme
security = HTTPBearer()

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Extract and validate the current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        scopes: list[str] = payload.get("scopes", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return TokenData(user_id=user_id, email=email, scopes=scopes)
        
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_data: TokenData = Depends(get_current_user_token)):
    """
    Get the current authenticated user from the database.
    
    Args:
        token_data: Token data from JWT
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If user not found or inactive
    """
    from app.db.client import database
    from app.db.models.auth.user import User, UserStatus
    
    try:
        user_id = ObjectId(token_data.user_id)
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