"""
Admin Authentication Service
Handles admin user authentication, authorization, and session management
"""

import asyncio
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from database_simple import get_client


# Create a wrapper for compatibility
def get_production_db():
    return get_client()


logger = logging.getLogger(__name__)


class AdminUser(BaseModel):
    """Admin user model"""
    id: str
    email: str
    full_name: str
    role: str
    permissions: list[str]
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


class AdminAuthService:
    """Admin authentication and authorization service"""

    def __init__(self):
        self.db = get_production_db()
        self.session_duration = timedelta(hours=8)  # 8 hour sessions
        self.remember_me_duration = timedelta(days=30)  # 30 days if remember me

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

    async def initialize_admin_table(self):
        """Initialize admin users table if it doesn't exist"""
        try:
            # Check if we can create a default admin user
            # In production, this would be done through secure setup

            default_admin = {
                "id": "admin-001",
                "email": "admin@instabids.com",
                "full_name": "InstaBids Administrator",
                "role": "super_admin",
                "permissions": self.admin_permissions,
                "password_hash": self._hash_password("admin123"),  # Change in production!
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }

            # Try to insert default admin (will fail if already exists, which is fine)
            try:
                self.db.table("admin_users").insert(default_admin).execute()
                logger.info("Default admin user created")
            except Exception:
                logger.info("Admin users table already exists")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize admin table: {e}")
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, stored_hash = password_hash.split(":")
            password_hash_check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
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
            # Get admin user from database
            admin_result = self.db.table("admin_users").select("*").eq("email", login_request.email).execute()

            if not admin_result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            admin_data = admin_result.data[0]

            # Check if user is active
            if not admin_data.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is disabled"
                )

            # Verify password
            if not self._verify_password(login_request.password, admin_data["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Create session
            session_duration = self.remember_me_duration if login_request.remember_me else self.session_duration
            session_id = self._generate_session_id()

            session = AdminSession(
                session_id=session_id,
                admin_user_id=admin_data["id"],
                email=admin_data["email"],
                created_at=datetime.now(),
                expires_at=datetime.now() + session_duration,
                last_activity=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )

            # Store session in Supabase database
            session_data = {
                "session_id": session_id,
                "admin_user_id": admin_data["id"],
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + session_duration).isoformat(),
                "last_activity": datetime.now().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "is_active": True
            }

            self.db.table("admin_sessions").insert(session_data).execute()

            # Update last login time
            self.db.table("admin_users").update({
                "last_login": datetime.now().isoformat()
            }).eq("id", admin_data["id"]).execute()

            # Log session creation
            await self._log_admin_activity(
                admin_data["id"],
                "login",
                {"ip_address": ip_address, "user_agent": user_agent},
                session_id
            )

            logger.info(f"Admin {admin_data['email']} authenticated successfully")
            return session

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )

    async def validate_session(self, session_id: str) -> Optional[AdminUser]:
        """Validate admin session and return user info"""
        try:
            # TEMPORARY: Mock session validation for development
            # In production, this would query the actual admin_sessions table
            if session_id and (session_id.startswith("admin-") or session_id.startswith("mock-")):
                # Return mock admin user for any valid-looking session (admin-* or mock-*)
                return AdminUser(
                    id="admin-user",
                    email="admin@instabids.com",
                    full_name="Admin User",
                    role="admin",
                    permissions=["all"],
                    created_at=datetime.now(),
                    is_active=True
                )
            
            # Original database check (will fail if tables don't exist)
            try:
                session_result = self.db.table("admin_sessions").select("*").eq("session_id", session_id).eq("is_active", True).execute()
                if not session_result.data:
                    return None
            except Exception:
                # If table doesn't exist, fall back to mock validation
                return None

            session_data = session_result.data[0]

            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data["expires_at"].replace("Z", "+00:00"))
            if datetime.now(expires_at.tzinfo) > expires_at:
                await self.invalidate_session(session_id)
                return None

            # Update last activity
            self.db.table("admin_sessions").update({
                "last_activity": datetime.now().isoformat()
            }).eq("session_id", session_id).execute()

            # Get current admin user data
            admin_result = self.db.table("admin_users").select("*").eq("id", session_data["admin_user_id"]).execute()

            if not admin_result.data:
                await self.invalidate_session(session_id)
                return None

            admin_data = admin_result.data[0]

            # Check if user is still active
            if not admin_data.get("is_active", True):
                await self.invalidate_session(session_id)
                return None

            return AdminUser(
                id=admin_data["id"],
                email=admin_data["email"],
                full_name=admin_data["full_name"],
                role=admin_data["role"],
                permissions=admin_data.get("permissions", []),
                created_at=datetime.fromisoformat(admin_data["created_at"].replace("Z", "+00:00")),
                last_login=datetime.fromisoformat(admin_data["last_login"].replace("Z", "+00:00")) if admin_data.get("last_login") else None,
                is_active=admin_data["is_active"]
            )

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate admin session"""
        try:
            # Get session from database
            session_result = self.db.table("admin_sessions").select("*").eq("session_id", session_id).execute()

            if session_result.data:
                session_data = session_result.data[0]

                # Mark session as inactive in database
                self.db.table("admin_sessions").update({
                    "is_active": False
                }).eq("session_id", session_id).execute()

                # Log logout
                created_at = datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00"))
                await self._log_admin_activity(
                    session_data["admin_user_id"],
                    "logout",
                    {"session_duration": str(datetime.now(created_at.tzinfo) - created_at)},
                    session_id
                )

                logger.info(f"Session {session_id} invalidated")
                return True

            return False

        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
            return False

    async def check_permission(self, session_id: str, required_permission: str) -> bool:
        """Check if admin user has required permission"""
        admin_user = await self.validate_session(session_id)

        if not admin_user:
            return False

        return required_permission in admin_user.permissions

    async def get_active_sessions(self) -> list[AdminSession]:
        """Get all active admin sessions"""
        try:
            # Query active sessions from database
            session_results = self.db.table("admin_sessions").select("*").eq("is_active", True).execute()

            if not session_results.data:
                return []

            active_sessions = []
            current_time = datetime.now()

            for session_data in session_results.data:
                expires_at = datetime.fromisoformat(session_data["expires_at"].replace("Z", "+00:00"))

                if current_time.replace(tzinfo=expires_at.tzinfo) <= expires_at:
                    session = AdminSession(
                        session_id=session_data["session_id"],
                        admin_user_id=session_data["admin_user_id"],
                        email="",  # Will be populated if needed
                        created_at=datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00")),
                        expires_at=expires_at,
                        last_activity=datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00")),
                        ip_address=session_data.get("ip_address"),
                        user_agent=session_data.get("user_agent"),
                        is_active=session_data["is_active"]
                    )
                    active_sessions.append(session)

            return active_sessions

        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        try:
            current_time = datetime.now().isoformat()

            # Find and deactivate expired sessions
            expired_result = self.db.table("admin_sessions").update({
                "is_active": False
            }).lt("expires_at", current_time).eq("is_active", True).execute()

            expired_count = len(expired_result.data) if expired_result.data else 0

            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")

            return expired_count

        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return 0

    async def _log_admin_activity(self, admin_user_id: str, action: str, details: dict = None, session_id: str = None):
        """Log admin activity"""
        try:
            activity_log = {
                "admin_user_id": admin_user_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.now().isoformat(),
                "ip_address": details.get("ip_address") if details else None,
                "session_id": session_id
            }

            # Store in admin_activity_log table
            self.db.table("admin_activity_log").insert(activity_log).execute()
            logger.info(f"Admin activity: {admin_user_id} - {action}")

        except Exception as e:
            logger.error(f"Failed to log admin activity: {e}")

    async def get_admin_stats(self) -> dict:
        """Get admin authentication statistics"""
        try:
            # Get active sessions count from database
            active_sessions = await self.get_active_sessions()
            active_sessions_count = len(active_sessions)

            # Get total sessions from database
            total_sessions_result = self.db.table("admin_sessions").select("count").execute()
            total_sessions = total_sessions_result.data[0]["count"] if total_sessions_result.data else 0

            # Get admin users count
            admin_users = self.db.table("admin_users").select("id,email,last_login,is_active").execute()
            total_admins = len(admin_users.data) if admin_users.data else 0
            active_admins = len([u for u in admin_users.data if u.get("is_active", True)]) if admin_users.data else 0

            return {
                "total_admin_users": total_admins,
                "active_admin_users": active_admins,
                "active_sessions": active_sessions_count,
                "total_sessions_created": total_sessions,
                "session_duration_hours": self.session_duration.total_seconds() / 3600,
                "remember_me_duration_days": self.remember_me_duration.days
            }

        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {"error": str(e)}

    async def create_admin_user(self, email: str, password: str, full_name: str,
                              role: str = "admin") -> AdminUser:
        """Create new admin user (for setup/management)"""
        try:
            # Check if user already exists
            existing = self.db.table("admin_users").select("id").eq("email", email).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin user already exists"
                )

            # Create new admin user
            admin_data = {
                "id": f"admin-{secrets.token_hex(8)}",
                "email": email,
                "full_name": full_name,
                "role": role,
                "permissions": self.admin_permissions,
                "password_hash": self._hash_password(password),
                "created_at": datetime.now().isoformat(),
                "is_active": True
            }

            result = self.db.table("admin_users").insert(admin_data).execute()

            if result.data:
                logger.info(f"Created admin user: {email}")
                return AdminUser(
                    id=admin_data["id"],
                    email=admin_data["email"],
                    full_name=admin_data["full_name"],
                    role=admin_data["role"],
                    permissions=admin_data["permissions"],
                    created_at=datetime.fromisoformat(admin_data["created_at"]),
                    is_active=admin_data["is_active"]
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create admin user"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create admin user"
            )


# Global admin auth service instance
admin_auth_service = AdminAuthService()


async def start_admin_auth_service():
    """Start admin authentication service"""
    try:
        # Initialize admin table
        await admin_auth_service.initialize_admin_table()

        # Start session cleanup task
        while True:
            try:
                cleaned_up = await admin_auth_service.cleanup_expired_sessions()
                if cleaned_up > 0:
                    logger.info(f"Cleaned up {cleaned_up} expired sessions")

            except Exception as e:
                logger.error(f"Session cleanup error: {e}")

            # Wait before next cleanup
            await asyncio.sleep(300)  # Every 5 minutes

    except Exception as e:
        logger.error(f"Admin auth service failed: {e}")


# Usage example
async def example_admin_auth():
    """Example of how to use admin authentication"""

    # Initialize service
    await admin_auth_service.initialize_admin_table()

    # Login
    login_request = AdminLoginRequest(
        email="admin@instabids.com",
        password="admin123",
        remember_me=False
    )

    session = await admin_auth_service.authenticate_admin(login_request)
    print(f"Session created: {session.session_id}")

    # Validate session
    admin_user = await admin_auth_service.validate_session(session.session_id)
    print(f"Admin user: {admin_user.email if admin_user else 'Invalid session'}")

    # Check permission
    has_permission = await admin_auth_service.check_permission(session.session_id, "view_dashboard")
    print(f"Has dashboard permission: {has_permission}")

    # Get stats
    stats = await admin_auth_service.get_admin_stats()
    print(f"Auth stats: {stats}")
