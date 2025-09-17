"""
Contractor Notification API
Provides endpoints for contractors to view and manage their notifications
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from database import SupabaseDB

# Create router
router = APIRouter()

# Database connection
db = SupabaseDB()


@router.get("/contractor/{contractor_id}/bid-card-changes")
async def get_contractor_bid_card_notifications(contractor_id: str):
    """Get bid card change notifications for a contractor"""
    try:
        # Get notifications where user_id matches contractor (from notifications table)
        result = db.client.table("notifications").select("*").eq(
            "user_id", contractor_id
        ).eq("notification_type", "bid_card_change").order(
            "created_at", desc=True
        ).execute()
        
        notifications = []
        for notification in result.data or []:
            notifications.append({
                "id": notification["id"],
                "title": notification["title"],
                "message": notification["message"],
                "notification_type": notification["notification_type"],
                "bid_card_id": notification["bid_card_id"],
                "action_url": notification["action_url"],
                "created_at": notification["created_at"],
                "is_read": notification["is_read"],
                "channels": notification.get("channels", {"email": True, "in_app": True, "sms": False})
            })
        
        return {
            "success": True,
            "notifications": notifications,
            "total": len(notifications)
        }
        
    except Exception as e:
        print(f"Error loading contractor bid card notifications: {e}")
        raise HTTPException(500, f"Failed to load notifications: {str(e)}")


@router.post("/{notification_id}/mark-read")
async def mark_notification_as_read(notification_id: str):
    """Mark a notification as read"""
    try:
        result = db.client.table("notifications").update({
            "is_read": True,
            "read_at": "now()"
        }).eq("id", notification_id).execute()
        
        if not result.data:
            raise HTTPException(404, "Notification not found")
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        raise HTTPException(500, f"Failed to mark notification as read: {str(e)}")


@router.get("/contractor/{contractor_id}/all")
async def get_all_contractor_notifications(contractor_id: str):
    """Get all notifications for a contractor (both bid card changes and other types)"""
    try:
        result = db.client.table("notifications").select("*").eq(
            "user_id", contractor_id
        ).order("created_at", desc=True).execute()
        
        bid_card_notifications = []
        other_notifications = []
        
        for notification in result.data or []:
            notification_data = {
                "id": notification["id"],
                "title": notification.get("title", "Notification"),
                "message": notification.get("message", ""),
                "notification_type": notification["notification_type"],
                "bid_card_id": notification.get("bid_card_id"),
                "action_url": notification.get("action_url"),
                "created_at": notification["created_at"],
                "is_read": notification["is_read"],
                "channels": notification.get("channels", {"email": True, "in_app": True, "sms": False})
            }
            
            if notification["notification_type"] == "bid_card_change":
                bid_card_notifications.append(notification_data)
            else:
                other_notifications.append(notification_data)
        
        return {
            "success": True,
            "bid_card_notifications": bid_card_notifications,
            "other_notifications": other_notifications,
            "total": len(result.data or []),
            "unread_count": len([n for n in (result.data or []) if not n["is_read"]])
        }
        
    except Exception as e:
        print(f"Error loading contractor notifications: {e}")
        raise HTTPException(500, f"Failed to load notifications: {str(e)}")


@router.get("/contractor/{contractor_id}/stats")
async def get_contractor_notification_stats(contractor_id: str):
    """Get notification statistics for a contractor"""
    try:
        result = db.client.table("notifications").select(
            "notification_type, is_read"
        ).eq("user_id", contractor_id).execute()
        
        stats = {
            "total": 0,
            "unread": 0,
            "bid_card_changes": 0,
            "bid_card_changes_unread": 0,
            "other": 0,
            "other_unread": 0
        }
        
        for notification in result.data or []:
            stats["total"] += 1
            if not notification["is_read"]:
                stats["unread"] += 1
            
            if notification["notification_type"] == "bid_card_change":
                stats["bid_card_changes"] += 1
                if not notification["is_read"]:
                    stats["bid_card_changes_unread"] += 1
            else:
                stats["other"] += 1
                if not notification["is_read"]:
                    stats["other_unread"] += 1
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        print(f"Error loading notification stats: {e}")
        raise HTTPException(500, f"Failed to load notification stats: {str(e)}")