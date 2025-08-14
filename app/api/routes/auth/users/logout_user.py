"""User logout endpoint."""

from fastapi import APIRouter, Response, Depends, Request
from app.services.auth.utils.session_auth import clear_session_cookie, get_current_user, invalidate_session_token
from app.core.logger import logger

router = APIRouter()

@router.post("/logout")
async def logout_user(request: Request, response: Response, current_user = Depends(get_current_user)):
    """
    Logout user and clear session cookie.
    """
    try:
        # Get the session token from cookies
        session_token = request.cookies.get("session_token")
        
        # Invalidate the session token if it exists
        if session_token:
            invalidate_session_token(session_token)
        
        # Clear the session cookie
        clear_session_cookie(response)
        
        logger.info(f"User {current_user.email} logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still clear the cookie even if there's an error
        clear_session_cookie(response)
        return {"message": "Logged out successfully"} 