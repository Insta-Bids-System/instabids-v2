"""
Temporary Admin Authentication Service
Provides admin authentication without requiring database table
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AdminUser(BaseModel):
    """Admin user model"""
    id: str
    email: str
    full_name: str
    role: str
    permissions: list
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class AdminSession(BaseModel):
    """Admin session model"""
    session_id: str
    admin_user_id: str
    email: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True

class AdminLoginRequest(BaseModel):
    """Admin login request model"""
    email: str
    password: str
    remember_me: bool = False

class TempAdminAuthService:
    """Temporary admin authentication service"""
    
    def __init__(self):
        self.session_duration = timedelta(hours=8)
        self.remember_me_duration = timedelta(days=30)
        self.active_sessions: Dict[str, AdminSession] = {}
        
        # Admin permissions
        self.admin_permissions = [
            "view_dashboard",
            "monitor_agents", 
            "control_campaigns",
            "view_database",
            "manage_system", 
            "export_data",
            "manage_users"
        ]
        
        # Hardcoded admin user for testing
        self.temp_admin = {
            "id": "admin-001",
            "email": "admin@instabids.com",
            "full_name": "InstaBids Administrator",
            "role": "super_admin",
            "permissions": self.admin_permissions,
            "password_hash": self._hash_password("admin123"),
            "created_at": datetime.now().isoformat(),
            "is_active": True
        }
        
        logger.info("Temporary admin auth service initialized")

    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return stored_hash == password_hash_check.hex()
        except Exception:
            return False

    def _generate_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)

    async def authenticate_admin(self, login_request: AdminLoginRequest, 
                               ip_address: str = None, user_agent: str = None) -> AdminSession:
        """Authenticate admin user and create session"""
        try:
            # Check credentials against temp admin
            if login_request.email != self.temp_admin["email"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Verify password
            if not self._verify_password(login_request.password, self.temp_admin["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Create session
            session_duration = self.remember_me_duration if login_request.remember_me else self.session_duration
            session_id = self._generate_session_id()

            session = AdminSession(
                session_id=session_id,
                admin_user_id=self.temp_admin["id"],
                email=self.temp_admin["email"],
                created_at=datetime.now(),
                expires_at=datetime.now() + session_duration,
                last_activity=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )

            # Store session in memory
            self.active_sessions[session_id] = session

            logger.info(f"Admin {self.temp_admin['email']} authenticated successfully")
            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    async def validate_session(self, session_id: str) -> Optional[dict]:
        """Validate admin session and return user info"""
        try:
            if session_id not in self.active_sessions:
                return None

            session = self.active_sessions[session_id]

            # Check if session is expired
            if datetime.now() > session.expires_at:
                await self.invalidate_session(session_id)
                return None

            # Check if session is active
            if not session.is_active:
                return None

            # Update last activity
            session.last_activity = datetime.now()

            admin_user = AdminUser(
                id=self.temp_admin["id"],
                email=self.temp_admin["email"],
                full_name=self.temp_admin["full_name"],
                role=self.temp_admin["role"],
                permissions=self.temp_admin["permissions"],
                created_at=datetime.fromisoformat(self.temp_admin["created_at"]),
                is_active=self.temp_admin["is_active"]
            )

            # Return session data with admin_user included
            return {
                "session": session,
                "admin_user": admin_user.dict()
            }

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate admin session"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Session {session_id} invalidated")
                return True
            return False
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False

    async def get_admin_stats(self) -> dict:
        """Get admin authentication statistics"""
        try:
            active_sessions_count = len([s for s in self.active_sessions.values() 
                                       if s.is_active and datetime.now() <= s.expires_at])

            return {
                "total_admin_users": 1,  # Only temp admin
                "active_admin_users": 1,
                "active_sessions": active_sessions_count,
                "total_sessions_created": len(self.active_sessions),
                "session_duration_hours": self.session_duration.total_seconds() / 3600,
                "remember_me_duration_days": self.remember_me_duration.days,
                "note": "Using temporary in-memory admin for testing"
            }

        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {"error": str(e)}

# Global temp admin auth service instance
temp_admin_auth_service = TempAdminAuthService()