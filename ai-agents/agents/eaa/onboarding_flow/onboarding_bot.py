"""
Onboarding Bot for EAA
Automated contractor onboarding and profile building
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional


class OnboardingBot:
    """Automated contractor onboarding system"""

    def __init__(self):
        """Initialize onboarding bot"""
        self.onboarding_stages = [
            "contacted",
            "interested",
            "info_collection",
            "verification",
            "profile_creation",
            "onboarded"
        ]

        self.required_info = {
            "basic": ["company_name", "contact_name", "email", "phone"],
            "business": ["license_number", "insurance_info", "years_in_business"],
            "services": ["specialties", "service_areas", "project_size_range"],
            "verification": ["license_verified", "insurance_verified", "references_checked"]
        }

        print("[OnboardingBot] Initialized with automated onboarding flow")

    def start_onboarding(self, contractor_email: str, source_campaign: str | None = None) -> dict[str, Any]:
        """
        Start onboarding process for interested contractor

        Args:
            contractor_email: Contractor's email address
            source_campaign: Campaign that generated the lead

        Returns:
            Onboarding initialization result
        """
        try:
            # Generate onboarding ID
            onboarding_id = str(uuid.uuid4())

            # Check if contractor already exists
            existing_contractor = self._check_existing_contractor(contractor_email)

            if existing_contractor:
                return self._handle_existing_contractor(existing_contractor, onboarding_id)

            # Create new onboarding record
            onboarding_record = {
                "id": onboarding_id,
                "contractor_email": contractor_email,
                "source_campaign": source_campaign,
                "stage": "contacted",
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "info_collected": {},
                "verification_status": {},
                "next_steps": []
            }

            # Send welcome message
            welcome_result = self._send_welcome_message(contractor_email, onboarding_id)

            if welcome_result["success"]:
                # Save onboarding record
                self._save_onboarding_record(onboarding_record)

                # Schedule follow-up
                self._schedule_onboarding_follow_up(onboarding_id, "initial", 24)

                result = {
                    "success": True,
                    "onboarding_id": onboarding_id,
                    "stage": "contacted",
                    "next_step": "awaiting_welcome_response",
                    "estimated_completion": self._estimate_completion_time(),
                    "welcome_sent": True
                }

                print(f"[OnboardingBot] Started onboarding for {contractor_email}")
                return result
            else:
                return {
                    "success": False,
                    "error": "Failed to send welcome message",
                    "details": welcome_result.get("error")
                }

        except Exception as e:
            print(f"[OnboardingBot ERROR] Failed to start onboarding: {e}")
            return {
                "success": False,
                "error": str(e),
                "onboarding_id": None
            }

    def process_onboarding_response(self, onboarding_id: str, response_data: dict[str, Any]) -> dict[str, Any]:
        """Process response from contractor during onboarding"""
        try:
            # Load onboarding record
            onboarding_record = self._load_onboarding_record(onboarding_id)

            if not onboarding_record:
                return {"success": False, "error": "Onboarding record not found"}

            current_stage = onboarding_record["stage"]

            # Process response based on current stage
            if current_stage == "contacted":
                return self._process_initial_response(onboarding_record, response_data)
            elif current_stage == "interested":
                return self._process_info_collection_response(onboarding_record, response_data)
            elif current_stage == "info_collection":
                return self._process_verification_response(onboarding_record, response_data)
            elif current_stage == "verification":
                return self._process_final_setup_response(onboarding_record, response_data)
            else:
                return {"success": False, "error": f"Unknown stage: {current_stage}"}

        except Exception as e:
            print(f"[OnboardingBot ERROR] Failed to process response: {e}")
            return {"success": False, "error": str(e)}

    def _process_initial_response(self, onboarding_record: dict[str, Any],
                                 response_data: dict[str, Any]) -> dict[str, Any]:
        """Process initial welcome response"""
        response_content = response_data.get("content", "").lower()

        # Check for positive response
        if any(keyword in response_content for keyword in ["yes", "interested", "tell me more", "sure"]):
            # Move to interested stage
            onboarding_record["stage"] = "interested"
            onboarding_record["last_activity"] = datetime.now().isoformat()

            # Send information collection form
            form_result = self._send_info_collection_form(onboarding_record)

            if form_result["success"]:
                self._save_onboarding_record(onboarding_record)
                return {
                    "success": True,
                    "stage_updated": "interested",
                    "next_step": "info_collection_sent",
                    "form_link": form_result["form_link"]
                }
            else:
                return {"success": False, "error": "Failed to send collection form"}

        # Check for negative response
        elif any(keyword in response_content for keyword in ["no", "not interested", "pass"]):
            onboarding_record["stage"] = "declined"
            onboarding_record["declined_at"] = datetime.now().isoformat()
            self._save_onboarding_record(onboarding_record)

            return {
                "success": True,
                "stage_updated": "declined",
                "next_step": "onboarding_ended"
            }

        # Unclear response - send clarification
        else:
            clarification_result = self._send_clarification_message(onboarding_record)
            return {
                "success": True,
                "stage_updated": "contacted",
                "next_step": "clarification_sent",
                "clarification_sent": clarification_result["success"]
            }

    def _process_info_collection_response(self, onboarding_record: dict[str, Any],
                                        response_data: dict[str, Any]) -> dict[str, Any]:
        """Process information collection form submission"""
        # Extract form data
        form_data = response_data.get("form_data", {})

        # Validate required fields
        missing_fields = self._validate_required_info(form_data)

        if missing_fields:
            # Request missing information
            self._request_missing_info(onboarding_record, missing_fields)
            return {
                "success": True,
                "stage_updated": "info_collection",
                "next_step": "missing_info_requested",
                "missing_fields": missing_fields
            }

        # Save collected information
        onboarding_record["info_collected"] = form_data
        onboarding_record["stage"] = "verification"
        onboarding_record["last_activity"] = datetime.now().isoformat()

        # Start verification process
        verification_result = self._start_verification(onboarding_record)

        self._save_onboarding_record(onboarding_record)

        return {
            "success": True,
            "stage_updated": "verification",
            "next_step": "verification_started",
            "verification_initiated": verification_result["success"]
        }

    def _send_welcome_message(self, contractor_email: str, onboarding_id: str) -> dict[str, Any]:
        """Send welcome message to start onboarding"""
        welcome_message = """
        Subject: Welcome to Instabids - Let's Get You Set Up!

        Hi there!

        Thank you for your interest in the project opportunity we shared with you.
        We're excited to potentially work together!

        To get started, we'd like to learn more about your business and set up
        your contractor profile on Instabids. This will help us match you with
        the best projects for your skills and availability.

        The setup process takes just 5-10 minutes and includes:
        ✓ Basic business information
        ✓ Services and specialties
        ✓ Service areas
        ✓ License and insurance verification

        Are you interested in getting started? Simply reply "YES" and we'll
        send you the next steps!

        Best regards,
        The Instabids Team

        P.S. Once you're set up, you'll have access to quality projects in your
        area with pre-qualified homeowners ready to hire.
        """

        # Mock sending email (in production, use actual email service)
        print(f"[OnboardingBot] Sending welcome message to {contractor_email}")
        print(f"Message: {welcome_message[:200]}...")

        return {
            "success": True,
            "message_id": f"welcome_{onboarding_id}",
            "sent_at": datetime.now().isoformat()
        }

    def _send_info_collection_form(self, onboarding_record: dict[str, Any]) -> dict[str, Any]:
        """Send information collection form"""
        contractor_email = onboarding_record["contractor_email"]
        onboarding_id = onboarding_record["id"]

        form_link = f"https://instabids.com/onboarding/{onboarding_id}"


        print(f"[OnboardingBot] Sending collection form to {contractor_email}")
        print(f"Form link: {form_link}")

        return {
            "success": True,
            "form_link": form_link,
            "message_id": f"form_{onboarding_id}",
            "sent_at": datetime.now().isoformat()
        }

    def _validate_required_info(self, form_data: dict[str, Any]) -> list[str]:
        """Validate required information is complete"""
        missing_fields = []

        for category, fields in self.required_info.items():
            if category == "verification":  # Skip verification fields
                continue

            for field in fields:
                if not form_data.get(field):
                    missing_fields.append(field)

        return missing_fields

    def _start_verification(self, onboarding_record: dict[str, Any]) -> dict[str, Any]:
        """Start verification process"""
        info = onboarding_record["info_collected"]

        verification_tasks = []

        # License verification
        if info.get("license_number"):
            verification_tasks.append("license_verification")

        # Insurance verification
        if info.get("insurance_info"):
            verification_tasks.append("insurance_verification")

        # Reference checks (optional)
        if info.get("references"):
            verification_tasks.append("reference_checks")

        # Mock verification process
        verification_status = {
            "license_verified": False,
            "insurance_verified": False,
            "references_checked": False,
            "verification_started_at": datetime.now().isoformat(),
            "tasks": verification_tasks
        }

        onboarding_record["verification_status"] = verification_status

        print(f"[OnboardingBot] Started verification with tasks: {verification_tasks}")

        return {
            "success": True,
            "verification_tasks": verification_tasks,
            "estimated_completion": "2-3 business days"
        }

    def get_onboarding_status(self, onboarding_id: str) -> dict[str, Any]:
        """Get current onboarding status"""
        try:
            onboarding_record = self._load_onboarding_record(onboarding_id)

            if not onboarding_record:
                return {"success": False, "error": "Onboarding record not found"}

            # Calculate progress percentage
            progress = self._calculate_progress(onboarding_record)

            # Get next steps
            next_steps = self._get_next_steps(onboarding_record)

            status = {
                "success": True,
                "onboarding_id": onboarding_id,
                "contractor_email": onboarding_record["contractor_email"],
                "current_stage": onboarding_record["stage"],
                "progress_percent": progress,
                "started_at": onboarding_record["started_at"],
                "last_activity": onboarding_record["last_activity"],
                "next_steps": next_steps,
                "estimated_completion": self._estimate_remaining_time(onboarding_record)
            }

            return status

        except Exception as e:
            print(f"[OnboardingBot ERROR] Failed to get status: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_progress(self, onboarding_record: dict[str, Any]) -> float:
        """Calculate onboarding progress percentage"""
        stage = onboarding_record["stage"]

        stage_progress = {
            "contacted": 10.0,
            "interested": 25.0,
            "info_collection": 50.0,
            "verification": 75.0,
            "profile_creation": 90.0,
            "onboarded": 100.0,
            "declined": 0.0
        }

        return stage_progress.get(stage, 0.0)

    def _get_next_steps(self, onboarding_record: dict[str, Any]) -> list[str]:
        """Get next steps for onboarding"""
        stage = onboarding_record["stage"]

        if stage == "contacted":
            return ["Respond to welcome message", "Confirm interest in setting up profile"]
        elif stage == "interested":
            return ["Complete information collection form", "Provide business details"]
        elif stage == "info_collection":
            return ["Wait for verification completion", "Respond to any verification requests"]
        elif stage == "verification":
            return ["Complete profile setup", "Review and confirm profile information"]
        elif stage == "profile_creation":
            return ["Finalize account setup", "Access contractor dashboard"]
        elif stage == "onboarded":
            return ["Profile complete - ready to receive projects!"]
        else:
            return ["Contact support for assistance"]

    # Helper methods
    def _check_existing_contractor(self, email: str) -> Optional[dict[str, Any]]:
        """Check if contractor already exists (mock implementation)"""
        # In production, query contractor database
        return None

    def _handle_existing_contractor(self, contractor: dict[str, Any], onboarding_id: str) -> dict[str, Any]:
        """Handle case where contractor already exists"""
        return {
            "success": True,
            "onboarding_id": onboarding_id,
            "existing_contractor": True,
            "contractor_id": contractor["id"],
            "message": "Contractor already exists in system"
        }

    def _save_onboarding_record(self, record: dict[str, Any]):
        """Save onboarding record (mock implementation)"""
        print(f"[OnboardingBot] Saving onboarding record for {record['contractor_email']}")

    def _load_onboarding_record(self, onboarding_id: str) -> Optional[dict[str, Any]]:
        """Load onboarding record (mock implementation)"""
        # Mock record for testing
        return {
            "id": onboarding_id,
            "contractor_email": "test@contractor.com",
            "stage": "contacted",
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "info_collected": {},
            "verification_status": {}
        }

    def _schedule_onboarding_follow_up(self, onboarding_id: str, follow_up_type: str, hours_delay: int):
        """Schedule follow-up message (mock implementation)"""
        follow_up_time = datetime.now() + timedelta(hours=hours_delay)
        print(f"[OnboardingBot] Scheduled {follow_up_type} follow-up for {follow_up_time}")

    def _estimate_completion_time(self) -> str:
        """Estimate total onboarding completion time"""
        return "3-5 business days"

    def _estimate_remaining_time(self, onboarding_record: dict[str, Any]) -> str:
        """Estimate remaining onboarding time"""
        stage = onboarding_record["stage"]

        remaining_time = {
            "contacted": "3-5 business days",
            "interested": "2-4 business days",
            "info_collection": "2-3 business days",
            "verification": "1-2 business days",
            "profile_creation": "1 business day",
            "onboarded": "Complete!"
        }

        return remaining_time.get(stage, "Unknown")

    def _send_clarification_message(self, onboarding_record: dict[str, Any]) -> dict[str, Any]:
        """Send clarification message for unclear responses"""
        print(f"[OnboardingBot] Sending clarification to {onboarding_record['contractor_email']}")
        return {"success": True}

    def _request_missing_info(self, onboarding_record: dict[str, Any], missing_fields: list[str]) -> dict[str, Any]:
        """Request missing information from contractor"""
        print(f"[OnboardingBot] Requesting missing info: {missing_fields}")
        return {"success": True}
