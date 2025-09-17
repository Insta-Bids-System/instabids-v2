"""
Session Authentication Middleware
Validates admin sessions from X-Session-ID header or session cookie
"""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status

from .auth_service import admin_auth_service


logger = logging.getLogger(__name__)


class SessionAuthMiddleware:
    """Middleware to validate admin sessions"""

    async def __call__(self, request: Request) -> Optional[str]:
        """Extract and validate session ID from request"""

        # Try to get session ID from X-Session-ID header first
        session_id = request.headers.get("X-Session-ID")

        # If not in header, try to get from cookie
        if not session_id:
            session_id = request.cookies.get("admin_session_id")

        # If not in cookie, try Authorization header
        if not session_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                session_id = auth_header.replace("Bearer ", "")

        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No session ID provided"
            )

        # Validate session
        admin_user = await admin_auth_service.validate_session(session_id)

        if not admin_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        # Store admin user in request state for use in endpoints
        request.state.admin_user = admin_user
        request.state.session_id = session_id

        return session_id


# Create global middleware instance
session_auth = SessionAuthMiddleware()


# Optional: Dependency for FastAPI routes
async def get_current_admin(request: Request):
    """Dependency to get current admin user from request"""
    if not hasattr(request.state, "admin_user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.admin_user


async def get_session_id(request: Request) -> str:
    """Dependency to get session ID from request"""
    if not hasattr(request.state, "session_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session ID"
        )
    return request.state.session_id
