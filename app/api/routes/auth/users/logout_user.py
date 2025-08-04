"""User logout endpoint."""

from fastapi import APIRouter, Response, status

from app.services.auth.utils.session_auth import clear_session_cookie
from app.core.logger import logger

router = APIRouter()

@router.post("/logout")
async def logout_user(response: Response):
    """
    Logout user by clearing session cookie.
    """
    try:
        # Clear session cookie
        clear_session_cookie(response)
        
        logger.info("User logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise 