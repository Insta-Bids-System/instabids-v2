"""
Email Channel for EAA
SendGrid integration for contractor outreach emails
"""
import os
import uuid
from datetime import datetime
from typing import Any


try:
    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("[EmailChannel] SendGrid not installed - using mock mode")


class EmailChannel:
    """Email communication channel using SendGrid"""

    def __init__(self):
        """Initialize email channel"""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("INSTABIDS_FROM_EMAIL", "noreply@instabids.com")

        if SENDGRID_AVAILABLE and self.api_key:
            self.sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            self.mode = "production"
            print("[EmailChannel] SendGrid initialized successfully")
        else:
            self.sg = None
            self.mode = "mock"
            print("[EmailChannel] Running in mock mode")

    def send_message(self, contractor: dict[str, Any], message_data: dict[str, Any],
                    campaign_id: str) -> dict[str, Any]:
        """
        Send email to contractor

        Args:
            contractor: Contractor information
            message_data: Email content and metadata
            campaign_id: Associated campaign ID

        Returns:
            Send result with message ID and status
        """
        try:
            contractor_email = contractor.get("email")
            if not contractor_email:
                return {
                    "success": False,
                    "error": "No email address provided",
                    "message_id": None
                }

            # Generate unique message ID
            message_id = str(uuid.uuid4())

            if self.mode == "production":
                result = self._send_production_email(
                    contractor_email, message_data, message_id, campaign_id
                )
            else:
                result = self._send_mock_email(
                    contractor_email, message_data, message_id, campaign_id
                )

            print(f"[EmailChannel] Email sent to {contractor_email}: {result['success']}")
            return result

        except Exception as e:
            print(f"[EmailChannel ERROR] Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message_id": None
            }

    def _send_production_email(self, to_email: str, message_data: dict[str, Any],
                              message_id: str, campaign_id: str) -> dict[str, Any]:
        """Send email via SendGrid"""
        try:
            # Create email object
            mail = Mail(
                from_email=Email(self.from_email, "Instabids Team"),
                to_emails=To(to_email),
                subject=message_data["subject"],
                html_content=Content("text/html", message_data["html_content"])
            )

            # Add custom headers for tracking
            mail.custom_args = {
                "message_id": message_id,
                "campaign_id": campaign_id,
                "channel": "email"
            }

            # Send email
            response = self.sg.client.mail.send.post(request_body=mail.get())

            if response.status_code in [200, 202]:
                return {
                    "success": True,
                    "message_id": message_id,
                    "sendgrid_message_id": response.headers.get("X-Message-Id"),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"SendGrid error: {response.status_code}",
                    "message_id": message_id
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"SendGrid exception: {e!s}",
                "message_id": message_id
            }

    def _send_mock_email(self, to_email: str, message_data: dict[str, Any],
                        message_id: str, campaign_id: str) -> dict[str, Any]:
        """Mock email sending for testing"""
        print(f"[EmailChannel MOCK] Sending email to {to_email}")
        print(f"Subject: {message_data['subject']}")
        print(f"Content preview: {message_data['html_content'][:100]}...")

        # Simulate successful send
        return {
            "success": True,
            "message_id": message_id,
            "mock_mode": True,
            "status_code": 202
        }

    def track_delivery(self, message_id: str) -> dict[str, Any]:
        """Track email delivery status"""
        try:
            if self.mode == "production":
                # In production, this would query SendGrid's Event API
                # For now, return mock data
                return {
                    "message_id": message_id,
                    "status": "delivered",
                    "delivered_at": datetime.now().isoformat(),
                    "opened": False,
                    "clicked": False
                }
            else:
                return {
                    "message_id": message_id,
                    "status": "delivered",
                    "delivered_at": datetime.now().isoformat(),
                    "mock_mode": True
                }

        except Exception as e:
            print(f"[EmailChannel ERROR] Failed to track delivery: {e}")
            return {
                "message_id": message_id,
                "status": "unknown",
                "error": str(e)
            }

    def handle_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Handle SendGrid webhook events"""
        try:
            event_type = webhook_data.get("event")
            message_id = webhook_data.get("message_id")

            if not message_id:
                return {"success": False, "error": "No message_id in webhook"}

            # Process different event types
            if event_type == "delivered":
                self._handle_delivery_event(webhook_data)
            elif event_type == "open":
                self._handle_open_event(webhook_data)
            elif event_type == "click":
                self._handle_click_event(webhook_data)
            elif event_type == "bounce":
                self._handle_bounce_event(webhook_data)
            elif event_type == "spam_report":
                self._handle_spam_event(webhook_data)

            return {"success": True, "event_processed": event_type}

        except Exception as e:
            print(f"[EmailChannel ERROR] Webhook processing failed: {e}")
            return {"success": False, "error": str(e)}

    def _handle_delivery_event(self, webhook_data: dict[str, Any]):
        """Handle email delivery confirmation"""
        message_id = webhook_data.get("message_id")
        print(f"[EmailChannel] Email {message_id} delivered successfully")
        # Update database with delivery status

    def _handle_open_event(self, webhook_data: dict[str, Any]):
        """Handle email open tracking"""
        message_id = webhook_data.get("message_id")
        print(f"[EmailChannel] Email {message_id} opened by recipient")
        # Update database with open status

    def _handle_click_event(self, webhook_data: dict[str, Any]):
        """Handle email link click tracking"""
        message_id = webhook_data.get("message_id")
        url = webhook_data.get("url")
        print(f"[EmailChannel] Link clicked in email {message_id}: {url}")
        # Update database with click data

    def _handle_bounce_event(self, webhook_data: dict[str, Any]):
        """Handle email bounce"""
        message_id = webhook_data.get("message_id")
        reason = webhook_data.get("reason")
        print(f"[EmailChannel] Email {message_id} bounced: {reason}")
        # Update database with bounce status

    def _handle_spam_event(self, webhook_data: dict[str, Any]):
        """Handle spam report"""
        message_id = webhook_data.get("message_id")
        print(f"[EmailChannel] Email {message_id} marked as spam")
        # Update database and potentially remove from future campaigns

    def get_templates(self) -> dict[str, str]:
        """Get available email templates"""
        return {
            "kitchen_urgent": "Urgent Kitchen Remodel Project",
            "bathroom_standard": "Bathroom Renovation Opportunity",
            "general_project": "New Project Opportunity",
            "follow_up": "Following Up - Project Opportunity"
        }
