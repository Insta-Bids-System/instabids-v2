"""
SMS Channel for EAA
Twilio integration for contractor outreach SMS
"""
import os
import uuid
from datetime import datetime
from typing import Any, Optional
from config.service_urls import get_backend_url


try:
    from twilio.base.exceptions import TwilioException
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("[SMSChannel] Twilio not installed - using mock mode")


class SMSChannel:
    """SMS communication channel using Twilio"""

    def __init__(self):
        """Initialize SMS channel"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")

        if TWILIO_AVAILABLE and self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.mode = "production"
            print("[SMSChannel] Twilio initialized successfully")
        else:
            self.client = None
            self.mode = "mock"
            print("[SMSChannel] Running in mock mode")

    def send_message(self, contractor: dict[str, Any], message_data: dict[str, Any],
                    campaign_id: str) -> dict[str, Any]:
        """
        Send SMS to contractor

        Args:
            contractor: Contractor information
            message_data: SMS content and metadata
            campaign_id: Associated campaign ID

        Returns:
            Send result with message ID and status
        """
        try:
            contractor_phone = contractor.get("phone")
            if not contractor_phone:
                return {
                    "success": False,
                    "error": "No phone number provided",
                    "message_id": None
                }

            # Generate unique message ID
            message_id = str(uuid.uuid4())

            # Clean phone number
            clean_phone = self._clean_phone_number(contractor_phone)
            if not clean_phone:
                return {
                    "success": False,
                    "error": "Invalid phone number format",
                    "message_id": None
                }

            if self.mode == "production":
                result = self._send_production_sms(
                    clean_phone, message_data, message_id, campaign_id
                )
            else:
                result = self._send_mock_sms(
                    clean_phone, message_data, message_id, campaign_id
                )

            print(f"[SMSChannel] SMS sent to {clean_phone}: {result['success']}")
            return result

        except Exception as e:
            print(f"[SMSChannel ERROR] Failed to send SMS: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": None
            }

    def _send_production_sms(self, to_phone: str, message_data: dict[str, Any],
                            message_id: str, campaign_id: str) -> dict[str, Any]:
        """Send SMS via Twilio"""
        try:
            # Create SMS message
            message = self.client.messages.create(
                body=message_data["content"],
                from_=self.from_number,
                to=to_phone,
                # Add webhook URL for delivery tracking
                status_callback=f"{os.getenv('BASE_URL', get_backend_url())}/api/eaa/webhook/sms-status"
            )

            return {
                "success": True,
                "message_id": message_id,
                "twilio_sid": message.sid,
                "status": message.status,
                "direction": message.direction
            }

        except TwilioException as e:
            return {
                "success": False,
                "error": f"Twilio error: {e!s}",
                "message_id": message_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SMS exception: {e!s}",
                "message_id": message_id
            }

    def _send_mock_sms(self, to_phone: str, message_data: dict[str, Any],
                      message_id: str, campaign_id: str) -> dict[str, Any]:
        """Mock SMS sending for testing"""
        print(f"[SMSChannel MOCK] Sending SMS to {to_phone}")
        print(f"Content: {message_data['content']}")

        # Simulate successful send
        return {
            "success": True,
            "message_id": message_id,
            "mock_mode": True,
            "status": "sent"
        }

    def _clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean and validate phone number"""
        if not phone:
            return None

        # Remove all non-digits
        digits_only = "".join(filter(str.isdigit, phone))

        # Handle US numbers
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        elif phone.startswith("+"):
            return phone
        else:
            return None

    def track_delivery(self, message_id: str, twilio_sid: str | None = None) -> dict[str, Any]:
        """Track SMS delivery status"""
        try:
            if self.mode == "production" and twilio_sid:
                # Query Twilio for message status
                message = self.client.messages(twilio_sid).fetch()

                return {
                    "message_id": message_id,
                    "twilio_sid": twilio_sid,
                    "status": message.status,
                    "error_code": message.error_code,
                    "error_message": message.error_message,
                    "price": message.price,
                    "direction": message.direction
                }
            else:
                return {
                    "message_id": message_id,
                    "status": "delivered",
                    "mock_mode": True
                }

        except Exception as e:
            print(f"[SMSChannel ERROR] Failed to track delivery: {e}")
            return {
                "message_id": message_id,
                "status": "unknown",
                "error": str(e)
            }

    def handle_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Handle Twilio webhook events"""
        try:
            message_sid = webhook_data.get("MessageSid")
            message_status = webhook_data.get("MessageStatus")

            if not message_sid:
                return {"success": False, "error": "No MessageSid in webhook"}

            # Process status update
            self._handle_status_update(message_sid, message_status, webhook_data)

            return {"success": True, "status_processed": message_status}

        except Exception as e:
            print(f"[SMSChannel ERROR] Webhook processing failed: {e}")
            return {"success": False, "error": str(e)}

    def handle_incoming_sms(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming SMS responses"""
        try:
            from_number = webhook_data.get("From")
            body = webhook_data.get("Body", "").strip()
            message_sid = webhook_data.get("MessageSid")

            print(f"[SMSChannel] Incoming SMS from {from_number}: {body}")

            # Process the response
            response_data = {
                "from_number": from_number,
                "content": body,
                "message_sid": message_sid,
                "received_at": datetime.now().isoformat(),
                "channel": "sms"
            }

            # Check for opt-out keywords
            if self._is_opt_out_message(body):
                self._handle_opt_out(from_number)
                return {
                    "success": True,
                    "action": "opt_out_processed",
                    "response_data": response_data
                }

            # Find original message this responds to
            original_message = self._find_original_message(from_number)

            if original_message:
                response_data["original_message_id"] = original_message["message_id"]
                response_data["campaign_id"] = original_message["campaign_id"]

            return {
                "success": True,
                "action": "response_received",
                "response_data": response_data
            }

        except Exception as e:
            print(f"[SMSChannel ERROR] Failed to handle incoming SMS: {e}")
            return {"success": False, "error": str(e)}

    def _handle_status_update(self, message_sid: str, status: str, webhook_data: dict[str, Any]):
        """Handle SMS status update"""
        print(f"[SMSChannel] Message {message_sid} status: {status}")

        if status == "delivered":
            print(f"[SMSChannel] SMS {message_sid} delivered successfully")
        elif status == "failed":
            error_code = webhook_data.get("ErrorCode")
            print(f"[SMSChannel] SMS {message_sid} failed with error {error_code}")
        elif status == "undelivered":
            print(f"[SMSChannel] SMS {message_sid} undelivered")

        # Update database with status

    def _is_opt_out_message(self, message_body: str) -> bool:
        """Check if message is an opt-out request"""
        opt_out_keywords = ["STOP", "UNSUBSCRIBE", "QUIT", "END", "CANCEL"]
        return message_body.upper().strip() in opt_out_keywords

    def _handle_opt_out(self, phone_number: str):
        """Handle opt-out request"""
        print(f"[SMSChannel] Processing opt-out for {phone_number}")
        # Add to opt-out list in database
        # Send confirmation SMS if required by regulations

    def _find_original_message(self, from_number: str) -> Optional[dict[str, Any]]:
        """Find the original outreach message this is responding to"""
        # In production, query database for recent messages to this number
        # For now, return mock data
        return {
            "message_id": "mock-message-123",
            "campaign_id": "mock-campaign-456",
            "sent_at": "2025-01-29T10:00:00Z"
        }

    def get_opt_out_list(self) -> list[str]:
        """Get list of opted-out phone numbers"""
        # In production, query database
        return []

    def is_opted_out(self, phone_number: str) -> bool:
        """Check if phone number has opted out"""
        clean_phone = self._clean_phone_number(phone_number)
        return clean_phone in self.get_opt_out_list()

    def get_templates(self) -> dict[str, str]:
        """Get available SMS templates"""
        return {
            "kitchen_urgent": "URGENT: Kitchen project in {location}. ${budget_min}-${budget_max}. Reply YES for details.",
            "bathroom_standard": "Bathroom renovation in {location}. ${budget_min}-${budget_max}. Interested? Reply YES.",
            "general_project": "{project_type} project available. ${budget_min}-${budget_max}. Reply YES for info.",
            "follow_up": "Still interested in the {project_type} project in {location}? Reply YES."
        }
