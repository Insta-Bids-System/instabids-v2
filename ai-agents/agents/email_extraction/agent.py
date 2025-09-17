"""
Email Extraction Agent (EEA)
Automated email extraction from contractor websites using Playwright
Fills missing email addresses in potential_contractors table
"""
import asyncio
import contextlib
import json
import os
import re
import time
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from supabase import create_client


class EmailExtractionAgent:
    """EEA - Extracts email addresses from contractor websites"""

    def __init__(self):
        """Initialize EEA with Playwright and Supabase"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Browser settings
        self.browser = None
        self.context = None
        self.headless = os.getenv("EEA_HEADLESS", "true").lower() == "true"

        # Email patterns
        self.email_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
        ]

        # Common contact page URLs
        self.contact_urls = [
            "contact", "contact-us", "contactus", "about", "about-us",
            "get-quote", "estimate", "info", "reach-us"
        ]

        print(f"[EEA] Initialized Email Extraction Agent (headless={self.headless})")

    def start_browser(self):
        """Start headless browser"""
        if not self.browser:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            print("[EEA] Browser started")

    def stop_browser(self):
        """Stop browser"""
        if self.browser:
            self.context.close()
            self.browser.close()
            self.browser = None
            self.context = None
            print("[EEA] Browser stopped")

    def extract_emails_from_contractors(self, limit: int = 10) -> dict[str, Any]:
        """
        Extract emails for contractors without email addresses

        Args:
            limit: Maximum number of contractors to process

        Returns:
            Dict with extraction results
        """
        try:
            print(f"[EEA] Starting email extraction for up to {limit} contractors")

            # Get contractors without emails but with websites
            contractors = self._get_contractors_needing_emails(limit)
            print(f"[EEA] Found {len(contractors)} contractors needing email extraction")

            if not contractors:
                return {"success": True, "message": "No contractors need email extraction", "extracted": 0}

            # Start browser
            self.start_browser()

            results = {
                "success": True,
                "total_processed": 0,
                "emails_found": 0,
                "emails_updated": 0,
                "contractors": []
            }

            for contractor in contractors:
                contractor_id = contractor["id"]
                company_name = contractor["company_name"]
                website = contractor["website"]

                print(f"[EEA] Processing: {company_name}")

                # Extract emails from website
                emails = self._extract_emails_from_website(website, company_name)

                contractor_result = {
                    "id": contractor_id,
                    "company_name": company_name,
                    "website": website,
                    "emails_found": emails,
                    "primary_email": emails[0] if emails else None,
                    "updated": False
                }

                # Update database if emails found
                if emails:
                    primary_email = emails[0]  # Use first/best email
                    updated = self._update_contractor_email(contractor_id, primary_email)
                    contractor_result["updated"] = updated

                    if updated:
                        results["emails_updated"] += 1
                        print(f"[EEA] ✓ Updated email for {company_name}: {primary_email}")

                    results["emails_found"] += 1
                else:
                    print(f"[EEA] ✗ No emails found for {company_name}")

                results["contractors"].append(contractor_result)
                results["total_processed"] += 1

                # Small delay between requests - TODO: Convert to async when method becomes async
                time.sleep(2)  # NOTE: Leave as sync until full agent conversion

            # Stop browser
            self.stop_browser()

            print(f"[EEA] Email extraction complete: {results['emails_found']}/{results['total_processed']} successful")
            return results

        except Exception as e:
            print(f"[EEA ERROR] Email extraction failed: {e}")
            self.stop_browser()
            return {"success": False, "error": str(e)}

    def _get_contractors_needing_emails(self, limit: int) -> list[dict[str, Any]]:
        """Get contractors without emails but with websites"""
        try:
            result = self.supabase.table("potential_contractors").select(
                "id,company_name,website,google_rating,google_review_count,match_score"
            ).is_("email", "null").not_.is_("website", "null").order(
                "match_score", desc=True
            ).limit(limit).execute()

            return result.data or []

        except Exception as e:
            print(f"[EEA ERROR] Failed to get contractors: {e}")
            return []

    def _extract_emails_from_website(self, website: str, company_name: str) -> list[str]:
        """Extract emails from a contractor website"""
        try:
            if not website or not website.startswith(("http://", "https://")):
                website = f"https://{website}" if website else ""

            if not website:
                return []

            print(f"[EEA] Scanning website: {website}")

            # Try main page first
            emails = self._scan_page_for_emails(website, company_name)

            # If no emails found on main page, try contact pages
            if not emails:
                emails = self._scan_contact_pages(website, company_name)

            # Clean and validate emails
            valid_emails = self._validate_emails(emails, company_name)

            return valid_emails

        except Exception as e:
            print(f"[EEA ERROR] Failed to extract from {website}: {e}")
            return []

    def _scan_page_for_emails(self, url: str, company_name: str) -> set[str]:
        """Scan a single page for email addresses"""
        emails = set()

        try:
            page = self.context.new_page()
            page.set_default_timeout(10000)  # 10 second timeout

            response = page.goto(url, wait_until="networkidle")

            if not response or response.status >= 400:
                print(f"[EEA] Failed to load {url}: {response.status if response else 'No response'}")
                page.close()
                return emails

            # Get page content
            content = page.content()

            # Extract emails using regex patterns
            for pattern in self.email_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        emails.add(match[0])  # mailto: pattern returns tuple
                    else:
                        emails.add(match)

            # Also check for emails in visible text
            try:
                visible_text = page.evaluate('document.body.innerText || document.body.textContent || ""')
                for pattern in self.email_patterns:
                    matches = re.findall(pattern, visible_text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            emails.add(match[0])
                        else:
                            emails.add(match)
            except:
                pass  # Continue if JavaScript fails

            page.close()
            print(f"[EEA] Found {len(emails)} emails on main page")

        except Exception as e:
            print(f"[EEA ERROR] Error scanning {url}: {e}")
            with contextlib.suppress(Exception):
                page.close()

        return emails

    def _scan_contact_pages(self, base_url: str, company_name: str) -> set[str]:
        """Scan contact pages for email addresses"""
        all_emails = set()

        for contact_path in self.contact_urls:
            try:
                # Try different URL combinations
                possible_urls = [
                    f"{base_url.rstrip('/')}/{contact_path}",
                    f"{base_url.rstrip('/')}/{contact_path}.html",
                    f"{base_url.rstrip('/')}/{contact_path}.php"
                ]

                for contact_url in possible_urls:
                    emails = self._scan_page_for_emails(contact_url, company_name)
                    all_emails.update(emails)

                    if emails:  # If we found emails, no need to try other variations
                        break

                    time.sleep(1)  # TODO: Convert to async when method becomes async

            except Exception:
                continue  # Try next contact page

        print(f"[EEA] Found {len(all_emails)} emails on contact pages")
        return all_emails

    def _validate_emails(self, emails: set[str], company_name: str) -> list[str]:
        """Clean and validate extracted emails"""
        valid_emails = []

        # Skip common unwanted emails
        skip_patterns = [
            r".*@example\.(com|org)",
            r".*@test\.(com|org)",
            r".*@placeholder\.(com|org)",
            r"noreply@.*",
            r"no-reply@.*",
            r".*@facebook\.com",
            r".*@instagram\.com",
            r".*@twitter\.com",
            r".*@linkedin\.com"
        ]

        for email in emails:
            email = email.lower().strip()

            # Skip if matches skip patterns
            if any(re.match(pattern, email, re.IGNORECASE) for pattern in skip_patterns):
                continue

            # Basic email validation
            if "@" in email and "." in email.split("@")[1]:
                valid_emails.append(email)

        # Sort by preference (info@, contact@, then others)
        def email_priority(email):
            if email.startswith("info@"):
                return 0
            elif email.startswith("contact@"):
                return 1
            elif any(email.startswith(prefix) for prefix in ["sales@", "admin@", "office@"]):
                return 2
            else:
                return 3

        valid_emails.sort(key=email_priority)

        print(f"[EEA] Validated {len(valid_emails)} emails: {valid_emails[:3]}...")
        return valid_emails

    def _update_contractor_email(self, contractor_id: str, email: str) -> bool:
        """Update contractor email in database"""
        try:
            result = self.supabase.table("potential_contractors").update({
                "email": email,
                "updated_at": datetime.now().isoformat()
            }).eq("id", contractor_id).execute()

            return bool(result.data)

        except Exception as e:
            print(f"[EEA ERROR] Failed to update email: {e}")
            return False

    def get_extraction_status(self) -> dict[str, Any]:
        """Get email extraction status for all contractors"""
        try:
            # Get total contractors
            total_result = self.supabase.table("potential_contractors").select("id").execute()
            total_contractors = len(total_result.data)

            # Get contractors with emails
            with_emails = self.supabase.table("potential_contractors").select("id").not_.is_("email", "null").execute()
            contractors_with_emails = len(with_emails.data)

            # Get contractors with websites but no emails
            need_extraction = self.supabase.table("potential_contractors").select("id").is_("email", "null").not_.is_("website", "null").execute()
            contractors_needing_extraction = len(need_extraction.data)

            return {
                "total_contractors": total_contractors,
                "with_emails": contractors_with_emails,
                "email_coverage": (contractors_with_emails / total_contractors * 100) if total_contractors > 0 else 0,
                "needing_extraction": contractors_needing_extraction,
                "status": "ready" if contractors_needing_extraction > 0 else "complete"
            }

        except Exception as e:
            print(f"[EEA ERROR] Failed to get status: {e}")
            return {"error": str(e)}


# Test the agent
if __name__ == "__main__":
    agent = EmailExtractionAgent()

    # Get status
    status = agent.get_extraction_status()
    print(f"Email Extraction Status: {json.dumps(status, indent=2)}")

    if status.get("needing_extraction", 0) > 0:
        print("\nStarting email extraction...")
        result = agent.extract_emails_from_contractors(limit=5)
        print(f"Extraction Result: {json.dumps(result, indent=2, default=str)}")
    else:
        print("No contractors need email extraction")
