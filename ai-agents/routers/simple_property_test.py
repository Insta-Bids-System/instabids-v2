"""
Simple property API test router to debug the issue
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/test-properties", tags=["Test Property System"])

@router.get("/")
async def test_root():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Test property API is working"}

@router.get("/health")
async def test_health():
    """Simple health check"""
    return {"status": "healthy", "service": "test_property_api"}

@router.get("/user/{user_id}")
async def test_get_user_properties(user_id: str):
    """Test user properties endpoint"""
    return {
        "user_id": user_id,
        "properties": [],
        "message": "Test endpoint working"
    }