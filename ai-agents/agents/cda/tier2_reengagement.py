"""
Tier 2: Re-engagement of Previous Contacts
Query previous outreach attempts for viable candidates
ENHANCED: Added radius-based geographical search using uszipcode + haversine
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Any

from supabase import Client


# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.radius_search_fixed import calculate_distance_miles


class Tier2Reengagement:
    """Tier 2 contractor re-engagement from outreach history"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def find_reengagement_candidates(self, bid_data: dict[str, Any], radius_miles: int = 15) -> list[dict[str, Any]]:
        """
        Find contractors for re-engagement from previous contacts within radius

        Uses optimized query from PRD with radius filtering:
        SELECT * FROM contractor_outreach
        WHERE contacted_date > (NOW() - INTERVAL '6 months')
          AND response_status != 'permanently_declined'
          AND project_match_score > 0.7
          AND contractor is within radius_miles of project location
          
        Args:
            bid_data: Bid card data with location and requirements
            radius_miles: Search radius in miles (default 15)
        """
        try:
            # Extract location data
            location = bid_data.get("location", {})
            zip_code = location.get("zip_code", "")

            if not zip_code:
                print("[Tier2 ERROR] No zip code provided in bid data")
                return []

            # Calculate 6 months ago threshold
            six_months_ago = datetime.now() - timedelta(days=180)
            six_months_iso = six_months_ago.isoformat()

            print(f"[Tier2] Searching outreach history since {six_months_ago.strftime('%Y-%m-%d')} within {radius_miles} miles of {zip_code}")

            # Query contractor outreach history
            query = self.supabase.table("contractor_outreach_attempts").select("""
                *,
                contractor_leads:contractor_lead_id (*)
            """)

            # Apply filters
            query = query.gte("sent_at", six_months_iso)
            query = query.neq("status", "opted_out")
            query = query.order("sent_at", desc=True)

            result = query.execute()
            outreach_records = result.data if result.data else []

            print(f"[Tier2] Found {len(outreach_records)} potential re-engagement candidates")

            # Process and score candidates with radius filtering
            candidates = []
            seen_contractors = set()

            for record in outreach_records:
                contractor_lead_id = record.get("contractor_lead_id")
                if not contractor_lead_id or contractor_lead_id in seen_contractors:
                    continue

                seen_contractors.add(contractor_lead_id)
                contractor = record.get("contractor_leads")

                if not contractor:
                    continue

                # Check if contractor is within radius of project location
                if not self._check_radius_location_match(contractor, zip_code, radius_miles):
                    continue

                # Calculate re-engagement viability
                reengagement_score = self._calculate_reengagement_score(record, bid_data)

                if reengagement_score > 0.5:  # Minimum threshold for re-engagement
                    # Add Tier 2 metadata
                    contractor["discovery_tier"] = 2
                    contractor["match_score"] = reengagement_score
                    contractor["reengagement_data"] = {
                        "last_contact": record.get("sent_at"),
                        "last_response": record.get("status"),
                        "contact_method": record.get("channel"),
                        "response_content": record.get("response_content", "")
                    }
                    contractor["match_reasons"] = self._get_reengagement_reasons(record, contractor, bid_data)

                    candidates.append(contractor)

            # Sort by distance first, then by reengagement score
            candidates.sort(key=lambda x: (x.get("distance_miles", 999), -x["match_score"]))

            print(f"[Tier2] After scoring: {len(candidates)} viable re-engagement candidates")

            # Return top 3 from Tier 2
            return candidates[:3]

        except Exception as e:
            print(f"[Tier2 ERROR] Failed to find re-engagement candidates: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _check_radius_location_match(self, contractor: dict[str, Any], project_zip: str, radius_miles: int) -> bool:
        """Check if contractor is within radius of project location using distance calculation"""
        try:
            # Get contractor's zip code
            contractor_zip = None

            # Try different zip code fields the contractor might have
            if contractor.get("zip_code"):
                contractor_zip = str(contractor["zip_code"]).strip()
            elif contractor.get("zip"):
                contractor_zip = str(contractor["zip"]).strip()
            elif contractor.get("postal_code"):
                contractor_zip = str(contractor["postal_code"]).strip()
            elif contractor.get("location_zip"):
                contractor_zip = str(contractor["location_zip"]).strip()

            if not contractor_zip:
                print(f"[Tier2] No zip code found for contractor {contractor.get('id', 'unknown')}")
                return False

            # Calculate distance between project and contractor
            distance = calculate_distance_miles(project_zip, contractor_zip)

            if distance is None:
                print(f"[Tier2] Could not calculate distance between {project_zip} and {contractor_zip}")
                return False

            # Add distance to contractor data for sorting
            contractor["distance_miles"] = distance

            # Check if within radius
            within_radius = distance <= radius_miles

            if within_radius:
                print(f"[Tier2] Previous contractor {contractor.get('company_name', 'Unknown')} is {distance} miles away (within {radius_miles} mile radius)")

            return within_radius

        except Exception as e:
            print(f"[Tier2] Error checking radius location match: {e}")
            return False

    def _calculate_reengagement_score(self, outreach_record: dict[str, Any], bid_data: dict[str, Any]) -> float:
        """Calculate re-engagement viability score"""
        score = 0.0

        # Base score (default 50 points for any previous contact)
        score += 50  

        # Response history bonus
        status = outreach_record.get("status", "")
        if status == "delivered" and outreach_record.get("response_content"):
            score += 30  # They responded
        elif status == "delivered":
            score += 15  # Delivered but no response
        elif status == "sent":
            score += 10  # At least sent successfully

        # Engagement bonus
        if outreach_record.get("opened_at"):
            score += 10  # They opened the message
        if outreach_record.get("clicked_at"):
            score += 15  # They clicked links

        # Recency bonus (more recent = better)
        sent_at_str = outreach_record.get("sent_at", "")
        try:
            sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00"))
            days_ago = (datetime.now() - sent_at.replace(tzinfo=None)).days

            if days_ago <= 30:
                score += 15  # Very recent
            elif days_ago <= 90:
                score += 10  # Recent
            elif days_ago <= 180:
                score += 5   # Somewhat recent
        except:
            pass

        # Contact method preference
        channel = outreach_record.get("channel", "")
        if channel == "phone":
            score += 5  # Phone contact shows more engagement
        elif channel == "email":
            score += 3  # Email is good

        return min(100.0, max(0.0, score))

    def _get_reengagement_reasons(self, outreach_record: dict[str, Any], contractor: dict[str, Any], bid_data: dict[str, Any]) -> list[str]:
        """Get human-readable re-engagement reasons"""
        reasons = []

        # Previous response
        status = outreach_record.get("status", "")
        if status == "delivered" and outreach_record.get("response_content"):
            reasons.append("Previously responded to outreach")
        elif status == "delivered":
            reasons.append("Previous message delivered successfully")

        # Engagement
        if outreach_record.get("opened_at"):
            reasons.append("Opened previous messages")
        if outreach_record.get("clicked_at"):
            reasons.append("Clicked links in previous messages")

        # Timing
        sent_at_str = outreach_record.get("sent_at", "")
        try:
            sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00"))
            days_ago = (datetime.now() - sent_at.replace(tzinfo=None)).days

            if days_ago <= 30:
                reasons.append("Recent contact (within 30 days)")
            elif days_ago <= 90:
                reasons.append("Recent contact (within 3 months)")
        except:
            pass

        # Contact quality
        response_content = outreach_record.get("response_content", "")
        if response_content and "interested" in response_content.lower():
            reasons.append("Showed interest in previous communication")
        if response_content and "busy" in response_content.lower():
            reasons.append("Was busy but may be available now")

        # Location with distance
        distance = contractor.get("distance_miles")
        city = contractor.get("city", "")
        state = contractor.get("state", "")

        if distance is not None:
            if city and state:
                reasons.append(f"Based in {city}, {state} ({distance} miles away)")
            else:
                reasons.append(f"{distance} miles away")
        elif city and state:
            reasons.append(f"Based in {city}, {state}")

        return reasons

    def create_outreach_record(self, contractor_id: str, bid_card_id: str, contact_method: str, project_match_score: float, notes: str = "") -> bool:
        """Create new outreach record for tracking"""
        try:
            record = {
                "contractor_id": contractor_id,
                "bid_card_id": bid_card_id,
                "contact_method": contact_method,
                "outreach_date": datetime.now().isoformat(),
                "response_status": "pending",
                "project_match_score": project_match_score,
                "notes": notes
            }

            result = self.supabase.table("contractor_outreach_attempts").insert(record).execute()
            return bool(result.data)

        except Exception as e:
            print(f"[Tier2 ERROR] Failed to create outreach record: {e}")
            return False
