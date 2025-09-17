"""
Tier 2: Re-engagement of Previous Contacts - UPDATED FOR REAL DATABASE
Query contractor_engagement_summary and contractor_outreach_attempts
"""
from datetime import datetime, timedelta
from typing import Any

from supabase import Client


class Tier2Reengagement:
    """Tier 2 contractor re-engagement from outreach history"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def find_reengagement_candidates(self, bid_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Find contractors for re-engagement from previous contacts

        Uses contractor_engagement_summary to find previously contacted leads
        that responded well but haven't been contacted recently
        """
        try:
            # Calculate thresholds
            thirty_days_ago = datetime.now() - timedelta(days=30)
            six_months_ago = datetime.now() - timedelta(days=180)

            print("[Tier2] Searching for re-engagement candidates (30+ days since contact)")

            # Query engagement summary for good candidates
            query = self.supabase.table("contractor_engagement_summary").select("""
                *,
                contractor_leads!inner(*)
            """)

            # Filter for good engagement history
            query = query.gte("engagement_score", 40)  # Decent engagement score
            query = query.gte("total_responses", 1)   # Has responded before
            query = query.lte("last_contacted_at", thirty_days_ago.isoformat())  # Not recently contacted
            query = query.gte("first_contacted_at", six_months_ago.isoformat())  # Not too old
            query = query.eq("opt_out_all", False)    # Not opted out

            # Order by engagement quality
            query = query.order("engagement_score", desc=True)
            query = query.order("positive_responses", desc=True)

            # Limit results
            query = query.limit(50)

            result = query.execute()
            engagement_records = result.data if result.data else []

            print(f"[Tier2] Found {len(engagement_records)} engagement records")

            # Process and score candidates
            candidates = []

            for record in engagement_records:
                contractor_lead = record.get("contractor_leads")

                if not contractor_lead:
                    continue

                # Check if contractor matches project requirements
                if not self._check_project_match(contractor_lead, bid_data):
                    continue

                # Calculate re-engagement viability
                reengagement_score = self._calculate_reengagement_score(record, contractor_lead, bid_data)

                if reengagement_score > 50:  # Minimum threshold for re-engagement
                    # Add Tier 2 metadata
                    contractor_lead["discovery_tier"] = 2
                    contractor_lead["match_score"] = reengagement_score
                    contractor_lead["reengagement_data"] = {
                        "last_contact": record.get("last_contacted_at"),
                        "total_contacts": record.get("total_outreach_count", 0),
                        "total_responses": record.get("total_responses", 0),
                        "positive_responses": record.get("positive_responses", 0),
                        "engagement_score": record.get("engagement_score", 0),
                        "preferred_channel": record.get("preferred_contact_channel", "email"),
                        "days_since_contact": record.get("days_since_last_contact", 0)
                    }
                    contractor_lead["match_reasons"] = self._get_reengagement_reasons(record, contractor_lead, bid_data)

                    candidates.append(contractor_lead)

            # Sort by reengagement score
            candidates.sort(key=lambda x: x["match_score"], reverse=True)

            print(f"[Tier2] After scoring: {len(candidates)} viable re-engagement candidates")

            # Return top candidates from Tier 2
            return {
                "success": True,
                "contractors": candidates[:8]
            }

        except Exception as e:
            print(f"[Tier2 ERROR] Failed to find re-engagement candidates: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "contractors": [],
                "error": str(e)
            }

    def _check_project_match(self, contractor_lead: dict[str, Any], bid_data: dict[str, Any]) -> bool:
        """Check if contractor matches project requirements"""
        # Location check
        project_state = bid_data.get("location", {}).get("state")
        if project_state and contractor_lead.get("state"):
            if project_state != contractor_lead["state"]:
                return False

        # Size preference check
        size_pref = bid_data.get("contractor_requirements", {}).get("contractor_size_preference")
        if size_pref and size_pref != "any":
            contractor_size = contractor_lead.get("contractor_size")
            if contractor_size:
                # Allow some flexibility
                size_options = self._get_flexible_sizes(size_pref)
                if contractor_size not in size_options:
                    return False

        # Specialty check
        project_type = bid_data.get("project_type", "").lower()
        specialties = contractor_lead.get("specialties", [])
        if specialties and project_type:
            # Check for match
            has_match = False
            for spec in specialties:
                if any(word in spec.lower() for word in project_type.split()):
                    has_match = True
                    break
            if not has_match:
                return False

        return True

    def _get_flexible_sizes(self, size_preference: str) -> list[str]:
        """Get flexible size options based on preference"""
        size_flexibility = {
            "solo_handyman": ["solo_handyman", "owner_operator"],
            "owner_operator": ["solo_handyman", "owner_operator", "small_business"],
            "small_business": ["owner_operator", "small_business", "regional_company"],
            "regional_company": ["small_business", "regional_company", "national_chain"],
            "national_chain": ["regional_company", "national_chain"]
        }
        return size_flexibility.get(size_preference, [size_preference])

    def _calculate_reengagement_score(self, engagement_record: dict[str, Any],
                                     contractor_lead: dict[str, Any],
                                     bid_data: dict[str, Any]) -> float:
        """Calculate re-engagement viability score"""
        score = 0.0

        # Base score from engagement history (40 points max)
        engagement_score = float(engagement_record.get("engagement_score", 0))
        score += engagement_score * 0.4  # Convert 0-100 to 0-40

        # Response rate bonus (20 points max)
        total_outreach = engagement_record.get("total_outreach_count", 0)
        total_responses = engagement_record.get("total_responses", 0)
        if total_outreach > 0:
            response_rate = total_responses / total_outreach
            score += response_rate * 20

        # Positive response bonus (20 points max)
        positive_responses = engagement_record.get("positive_responses", 0)
        if total_responses > 0:
            positive_rate = positive_responses / total_responses
            score += positive_rate * 20

        # Timing bonus (10 points max)
        days_since_contact = engagement_record.get("days_since_last_contact", 0)
        if 30 <= days_since_contact <= 60:
            score += 10  # Perfect timing - not too recent, not too old
        elif 60 < days_since_contact <= 90:
            score += 7
        elif 90 < days_since_contact <= 120:
            score += 4
        elif days_since_contact > 120:
            score += 2

        # Contractor quality bonus (10 points max)
        rating = float(contractor_lead.get("rating", 0))
        if rating >= 4.5:
            score += 10
        elif rating >= 4.0:
            score += 7
        elif rating >= 3.5:
            score += 4

        return min(100.0, max(0.0, score))

    def _get_reengagement_reasons(self, engagement_record: dict[str, Any],
                                  contractor_lead: dict[str, Any],
                                  bid_data: dict[str, Any]) -> list[str]:
        """Get human-readable re-engagement reasons"""
        reasons = []

        # Engagement history
        engagement_score = engagement_record.get("engagement_score", 0)
        if engagement_score >= 70:
            reasons.append("Excellent engagement history")
        elif engagement_score >= 50:
            reasons.append("Good engagement history")

        # Response history
        total_responses = engagement_record.get("total_responses", 0)
        positive_responses = engagement_record.get("positive_responses", 0)
        if positive_responses > 0:
            reasons.append(f"{positive_responses} positive responses")
        elif total_responses > 0:
            reasons.append(f"Responded {total_responses} times")

        # Timing
        days_since = engagement_record.get("days_since_last_contact", 0)
        if 30 <= days_since <= 60:
            reasons.append("Perfect re-engagement timing")
        elif days_since > 60:
            reasons.append(f"Last contacted {days_since} days ago")

        # Email engagement
        email_opened = engagement_record.get("email_opened_count", 0)
        email_clicked = engagement_record.get("email_clicked_count", 0)
        if email_clicked > 0:
            reasons.append(f"Clicked {email_clicked} email links")
        elif email_opened > 0:
            reasons.append(f"Opened {email_opened} emails")

        # Contractor details
        company = contractor_lead.get("company_name", "Contractor")
        rating = contractor_lead.get("rating", 0)
        if rating >= 4.0:
            reasons.append(f"{company} - {rating} star rating")
        else:
            reasons.append(company)

        # Preferred contact method
        preferred_channel = engagement_record.get("preferred_contact_channel")
        if preferred_channel:
            channel_names = {
                "email": "Email preferred",
                "sms": "SMS preferred",
                "phone": "Phone preferred",
                "website_form": "Website form preferred"
            }
            if preferred_channel in channel_names:
                reasons.append(channel_names[preferred_channel])

        return reasons

    def get_recent_outreach_attempts(self, contractor_lead_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Get recent outreach attempts for a contractor lead"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            result = self.supabase.table("contractor_outreach_attempts").select("*").eq(
                "contractor_lead_id", contractor_lead_id
            ).gte("sent_at", cutoff_date.isoformat()).order("sent_at", desc=True).execute()

            return result.data if result.data else []

        except Exception as e:
            print(f"[Tier2 ERROR] Failed to get outreach attempts: {e}")
            return []
