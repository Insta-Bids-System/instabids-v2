"""
Email Discovery Agent for Contractor Websites
Scrapes contractor websites to find email addresses and contact information
"""
import asyncio
import re
import time
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class EmailDiscoveryAgent:
    """Agent for discovering email addresses from contractor websites"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

        # Common email patterns
        self.email_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})",
        ]

        # Pages to check for contact info
        self.contact_pages = [
            "/",
            "/contact",
            "/contact-us",
            "/about",
            "/about-us",
            "/get-quote",
            "/quote",
            "/services"
        ]

        # Request headers to appear like a real browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        print("[EmailDiscoveryAgent] Initialized email discovery system")

    def discover_emails_for_contractors(self, contractor_ids: list[str]) -> dict[str, Any]:
        """
        Discover emails for a list of contractors

        Args:
            contractor_ids: List of contractor IDs to process

        Returns:
            Dict with discovery results
        """
        try:
            print(f"[EmailDiscoveryAgent] Starting email discovery for {len(contractor_ids)} contractors")

            results = {
                "total_processed": 0,
                "emails_found": 0,
                "contractors_updated": 0,
                "errors": [],
                "discoveries": []
            }

            for contractor_id in contractor_ids:
                try:
                    contractor = self._load_contractor(contractor_id)
                    if not contractor:
                        results["errors"].append(f"Contractor {contractor_id} not found")
                        continue

                    # Skip if already has email
                    if contractor.get("email"):
                        print(f"[EmailDiscoveryAgent] {contractor.get('company_name')} already has email")
                        results["total_processed"] += 1
                        continue

                    website = contractor.get("website")
                    if not website:
                        print(f"[EmailDiscoveryAgent] {contractor.get('company_name')} has no website")
                        results["total_processed"] += 1
                        continue

                    print(f"[EmailDiscoveryAgent] Discovering email for: {contractor.get('company_name')}")
                    print(f"[EmailDiscoveryAgent] Website: {website}")

                    # Discover email from website
                    discovery_result = self._discover_email_from_website(website, contractor.get("company_name", ""))

                    if discovery_result["success"] and discovery_result["emails"]:
                        # Update contractor with discovered email
                        primary_email = discovery_result["emails"][0]
                        update_result = self._update_contractor_email(contractor_id, primary_email, discovery_result)

                        if update_result:
                            results["emails_found"] += 1
                            results["contractors_updated"] += 1
                            results["discoveries"].append({
                                "contractor_id": contractor_id,
                                "company_name": contractor.get("company_name"),
                                "email": primary_email,
                                "source_page": discovery_result.get("source_page", "unknown")
                            })
                            print(f"[EmailDiscoveryAgent] SUCCESS: Found {primary_email} for {contractor.get('company_name')}")
                        else:
                            results["errors"].append(f"Failed to update {contractor.get('company_name')} with email")
                    else:
                        print(f"[EmailDiscoveryAgent] No email found for {contractor.get('company_name')}")

                    results["total_processed"] += 1

                    # Respectful delay between requests - convert to async if method becomes async
                    time.sleep(2)  # TODO: Make this async when method is converted

                except Exception as e:
                    error_msg = f"Error processing contractor {contractor_id}: {e}"
                    print(f"[EmailDiscoveryAgent ERROR] {error_msg}")
                    results["errors"].append(error_msg)
                    results["total_processed"] += 1

            print(f"[EmailDiscoveryAgent] Discovery complete: {results['emails_found']}/{results['total_processed']} emails found")
            return results

        except Exception as e:
            print(f"[EmailDiscoveryAgent ERROR] Discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_processed": 0,
                "emails_found": 0
            }

    def _discover_email_from_website(self, website_url: str, company_name: str) -> dict[str, Any]:
        """
        Discover email addresses from a contractor's website

        Args:
            website_url: The contractor's website URL
            company_name: Company name for filtering relevant emails

        Returns:
            Dict with discovery results
        """
        try:
            # Normalize URL
            if not website_url.startswith(("http://", "https://")):
                website_url = "https://" + website_url

            parsed_url = urlparse(website_url)
            base_domain = parsed_url.netloc.lower()

            emails_found = []
            pages_checked = []

            # Check multiple pages for contact information
            for page_path in self.contact_pages:
                try:
                    page_url = urljoin(website_url, page_path)

                    # Make request with timeout
                    response = requests.get(
                        page_url,
                        headers=self.headers,
                        timeout=10,
                        allow_redirects=True
                    )

                    if response.status_code == 200:
                        page_emails = self._extract_emails_from_html(response.text, base_domain)
                        if page_emails:
                            emails_found.extend(page_emails)
                            pages_checked.append({
                                "url": page_url,
                                "emails_found": len(page_emails),
                                "emails": page_emails
                            })

                        # Don't overload the server - convert to async if method becomes async
                        time.sleep(1)  # TODO: Make this async when method is converted

                except requests.exceptions.RequestException as e:
                    print(f"[EmailDiscoveryAgent] Error accessing {page_url}: {e}")
                    continue
                except Exception as e:
                    print(f"[EmailDiscoveryAgent] Error processing {page_url}: {e}")
                    continue

            # Remove duplicates and filter emails
            unique_emails = list(set(emails_found))
            filtered_emails = self._filter_relevant_emails(unique_emails, base_domain, company_name)

            return {
                "success": True,
                "website_url": website_url,
                "emails": filtered_emails,
                "pages_checked": pages_checked,
                "total_emails_found": len(unique_emails),
                "filtered_emails": len(filtered_emails),
                "source_page": pages_checked[0]["url"] if pages_checked else website_url
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "website_url": website_url,
                "emails": []
            }

    def _extract_emails_from_html(self, html_content: str, base_domain: str) -> list[str]:
        """Extract email addresses from HTML content"""
        emails = []

        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text_content = soup.get_text()

            # Extract emails using regex patterns
            for pattern in self.email_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if isinstance(matches[0] if matches else None, tuple):
                    # Handle patterns with groups (like mailto:)
                    emails.extend([match[0] if isinstance(match, tuple) else match for match in matches])
                else:
                    emails.extend(matches)

            # Also check href attributes for mailto links
            mailto_links = soup.find_all("a", href=re.compile(r"^mailto:", re.IGNORECASE))
            for link in mailto_links:
                href = link.get("href", "")
                email_match = re.search(r"mailto:([^?&\s]+)", href, re.IGNORECASE)
                if email_match:
                    emails.append(email_match.group(1))

            # Clean and validate emails
            cleaned_emails = []
            for email in emails:
                email = email.strip().lower()
                if self._is_valid_email(email):
                    cleaned_emails.append(email)

            return cleaned_emails

        except Exception as e:
            print(f"[EmailDiscoveryAgent] Error extracting emails from HTML: {e}")
            return []

    def _filter_relevant_emails(self, emails: list[str], base_domain: str, company_name: str) -> list[str]:
        """Filter emails to find the most relevant business contacts"""
        if not emails:
            return []

        # Remove common spam/generic domains
        spam_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
            "protonmail.com", "icloud.com", "live.com", "msn.com"
        ]

        # Score emails by relevance
        email_scores = []

        for email in emails:
            score = 0
            email_lower = email.lower()
            email_domain = email_lower.split("@")[-1]

            # Prefer emails from the company domain
            if base_domain in email_domain or email_domain in base_domain:
                score += 100

            # Avoid spam domains
            if email_domain in spam_domains:
                score -= 50

            # Prefer business-like email prefixes
            email_prefix = email_lower.split("@")[0]
            business_prefixes = [
                "info", "contact", "sales", "quotes", "office", "admin",
                "hello", "inquiries", "business", "service", "support"
            ]

            if any(prefix in email_prefix for prefix in business_prefixes):
                score += 30

            # Check if company name appears in email
            if company_name:
                company_words = company_name.lower().split()
                for word in company_words:
                    if len(word) > 3 and word in email_prefix:
                        score += 20

            # Avoid obvious non-business emails
            personal_indicators = ["noreply", "donotreply", "no-reply", "mailer", "automated"]
            if any(indicator in email_prefix for indicator in personal_indicators):
                score -= 100

            email_scores.append((email, score))

        # Sort by score and return top emails
        sorted_emails = sorted(email_scores, key=lambda x: x[1], reverse=True)

        # Return top 3 emails with positive scores
        return [email for email, score in sorted_emails if score > 0][:3]

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
        return bool(re.match(pattern, email))

    def _load_contractor(self, contractor_id: str) -> Optional[dict[str, Any]]:
        """Load contractor data from database"""
        try:
            # Try potential_contractors table first
            result = self.supabase.table("potential_contractors").select("*").eq("id", contractor_id).execute()

            if result.data:
                return result.data[0]

            # Try contractor_leads table
            result = self.supabase.table("contractor_leads").select("*").eq("id", contractor_id).execute()

            if result.data:
                return result.data[0]

            print(f"[EmailDiscoveryAgent] Contractor {contractor_id} not found in either table")
            return None

        except Exception as e:
            print(f"[EmailDiscoveryAgent] Error loading contractor {contractor_id}: {e}")
            return None

    def _update_contractor_email(self, contractor_id: str, email: str, discovery_result: dict) -> bool:
        """Update contractor record with discovered email"""
        try:
            update_data = {
                "email": email
            }

            # Try potential_contractors table first
            result = self.supabase.table("potential_contractors").update(update_data).eq("id", contractor_id).execute()

            if result.data:
                print(f"[EmailDiscoveryAgent] Updated potential_contractors table for {contractor_id}")
                return True

            # Try contractor_leads table
            result = self.supabase.table("contractor_leads").update(update_data).eq("id", contractor_id).execute()

            if result.data:
                print(f"[EmailDiscoveryAgent] Updated contractor_leads table for {contractor_id}")
                return True

            print(f"[EmailDiscoveryAgent] Failed to update either table for {contractor_id}")
            return False

        except Exception as e:
            print(f"[EmailDiscoveryAgent] Error updating contractor {contractor_id}: {e}")
            return False

    def get_contractors_needing_emails(self, project_zip_code: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Get contractors that need email discovery"""
        try:
            # Build query
            query = self.supabase.table("potential_contractors").select("*")

            # Filter by location if provided
            if project_zip_code:
                query = query.eq("project_zip_code", project_zip_code)

            # Filter for contractors without emails but with websites
            query = query.is_("email", "null").not_.is_("website", "null")

            # Limit results
            query = query.limit(limit)

            result = query.execute()

            return result.data if result.data else []

        except Exception as e:
            print(f"[EmailDiscoveryAgent] Error getting contractors needing emails: {e}")
            return []


# Test the email discovery agent
if __name__ == "__main__":
    import os

    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(override=True)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    supabase = create_client(supabase_url, supabase_key)

    agent = EmailDiscoveryAgent(supabase)

    print("Testing Email Discovery Agent...")

    # Get contractors needing emails
    contractors = agent.get_contractors_needing_emails(limit=5)

    if contractors:
        print(f"\nFound {len(contractors)} contractors needing email discovery")

        contractor_ids = [c["id"] for c in contractors]

        # Test email discovery
        result = agent.discover_emails_for_contractors(contractor_ids)

        print("\nEmail Discovery Results:")
        print(f"  Processed: {result['total_processed']}")
        print(f"  Emails Found: {result['emails_found']}")
        print(f"  Contractors Updated: {result['contractors_updated']}")

        if result["discoveries"]:
            print("\nDiscoveries:")
            for discovery in result["discoveries"]:
                print(f"  {discovery['company_name']}: {discovery['email']}")

        if result["errors"]:
            print(f"\nErrors: {result['errors']}")
    else:
        print("No contractors found needing email discovery")
