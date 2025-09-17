"""
WFA (Website Form Automation Agent)
Headless browser automation for filling contractor website contact forms
Priority #1 outreach method
"""
import json
import os
import time
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright
from supabase import create_client


class WebsiteFormAutomationAgent:
    """WFA - Automates filling contact forms on contractor websites"""

    def __init__(self):
        """Initialize WFA with Playwright and Supabase"""
        load_dotenv(override=True)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Browser settings
        self.browser = None
        self.context = None
        self.headless = os.getenv("WFA_HEADLESS", "true").lower() == "true"

        print(f"[WFA] Initialized Website Form Automation Agent (headless={self.headless})")

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
            print("[WFA] Browser started")

    def stop_browser(self):
        """Stop browser"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.context = None
            print("[WFA] Browser stopped")

    def analyze_website_for_form(self, contractor_lead: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze contractor website to find contact forms

        Returns:
            Dict with form analysis results
        """
        website = contractor_lead.get("website")
        if not website:
            return {
                "success": False,
                "error": "No website URL provided",
                "has_contact_form": False
            }

        # Ensure URL has protocol
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"

        try:
            self.start_browser()
            page = self.context.new_page()

            print(f"[WFA] Analyzing website: {website}")

            # Navigate to website
            page.goto(website, wait_until="networkidle", timeout=30000)

            # Common contact page patterns
            contact_urls = []

            # Look for contact links
            contact_link_patterns = [
                "contact", "contact-us", "get-in-touch", "request-quote",
                "get-quote", "free-estimate", "estimate", "inquiry"
            ]

            links = page.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href") or ""
                text = link.text_content() or ""

                for pattern in contact_link_patterns:
                    if pattern in href.lower() or pattern in text.lower():
                        full_url = self._make_absolute_url(href, website)
                        if full_url not in contact_urls:
                            contact_urls.append(full_url)

            # Check current page for forms
            forms_on_page = self._find_forms_on_page(page)

            # Visit contact pages and check for forms
            all_forms = forms_on_page.copy()
            for contact_url in contact_urls[:3]:  # Limit to 3 contact pages
                try:
                    page.goto(contact_url, wait_until="networkidle", timeout=20000)
                    page_forms = self._find_forms_on_page(page)
                    for form in page_forms:
                        form["page_url"] = contact_url
                        all_forms.append(form)
                except Exception as e:
                    print(f"[WFA] Error visiting {contact_url}: {e}")

            # Find best form
            best_form = self._select_best_form(all_forms)

            result = {
                "success": True,
                "website": website,
                "has_contact_form": len(all_forms) > 0,
                "forms_found": len(all_forms),
                "contact_pages": contact_urls,
                "best_form": best_form,
                "all_forms": all_forms
            }

            # Update contractor_leads with form info
            self._update_contractor_lead_form_info(contractor_lead["id"], result)

            page.close()
            return result

        except Exception as e:
            print(f"[WFA ERROR] Failed to analyze website: {e}")
            return {
                "success": False,
                "error": str(e),
                "has_contact_form": False
            }

    def _find_forms_on_page(self, page: Page) -> list[dict[str, Any]]:
        """Find all forms on a page"""
        forms = []

        # Find all form elements
        form_elements = page.query_selector_all("form")

        for i, form in enumerate(form_elements):
            form_data = {
                "form_index": i,
                "page_url": page.url,
                "fields": []
            }

            # Analyze form fields
            inputs = form.query_selector_all("input, textarea, select")

            for input_elem in inputs:
                field_type = input_elem.get_attribute("type") or "text"
                field_name = input_elem.get_attribute("name") or ""
                field_id = input_elem.get_attribute("id") or ""
                placeholder = input_elem.get_attribute("placeholder") or ""
                label = self._find_label_for_field(page, input_elem)
                required = input_elem.get_attribute("required") is not None

                # Skip hidden and submit fields
                if field_type in ["hidden", "submit", "button"]:
                    continue

                field_info = {
                    "type": field_type,
                    "name": field_name,
                    "id": field_id,
                    "placeholder": placeholder,
                    "label": label,
                    "required": required,
                    "tag": input_elem.evaluate("el => el.tagName").lower()
                }

                # Determine field purpose
                field_info["purpose"] = self._determine_field_purpose(field_info)
                form_data["fields"].append(field_info)

            # Calculate form score
            form_data["score"] = self._calculate_form_score(form_data)
            forms.append(form_data)

        return forms

    def _find_label_for_field(self, page: Page, field) -> str:
        """Find label text for a form field"""
        try:
            # Check for associated label
            field_id = field.get_attribute("id")
            if field_id:
                label = page.query_selector(f'label[for="{field_id}"]')
                if label:
                    return label.text_content().strip()

            # Check for parent label
            parent = field.evaluate("el => el.parentElement")
            if parent:
                parent_tag = field.evaluate("el => el.parentElement.tagName").lower()
                if parent_tag == "label":
                    return field.evaluate("el => el.parentElement.textContent").strip()

            # Check for nearby text
            return field.evaluate("""el => {
                const prev = el.previousSibling;
                if (prev && prev.nodeType === 3) return prev.textContent.trim();
                const prevEl = el.previousElementSibling;
                if (prevEl && prevEl.tagName === 'LABEL') return prevEl.textContent.trim();
                return '';
            }""")
        except:
            return ""

    def _determine_field_purpose(self, field_info: dict[str, Any]) -> str:
        """Determine the purpose of a form field"""
        # Combine all text clues
        clues = " ".join([
            field_info.get("name", ""),
            field_info.get("id", ""),
            field_info.get("placeholder", ""),
            field_info.get("label", "")
        ]).lower()

        # Field purpose patterns
        patterns = {
            "name": ["name", "fname", "first", "last", "lname", "fullname", "your name"],
            "email": ["email", "e-mail", "mail", "contact email"],
            "phone": ["phone", "tel", "mobile", "cell", "number", "contact number"],
            "company": ["company", "business", "organization", "org"],
            "message": ["message", "comments", "description", "details", "project", "tell us", "inquiry"],
            "address": ["address", "street", "location"],
            "city": ["city", "town"],
            "state": ["state", "province"],
            "zip": ["zip", "postal", "code"],
            "service": ["service", "type", "category", "what do you need"],
            "budget": ["budget", "price", "cost", "estimate"],
            "timeline": ["timeline", "when", "date", "timeframe"]
        }

        for purpose, keywords in patterns.items():
            if any(keyword in clues for keyword in keywords):
                return purpose

        # Check field type
        if field_info.get("type") == "email":
            return "email"
        elif field_info.get("type") == "tel":
            return "phone"
        elif field_info.get("tag") == "textarea":
            return "message"

        return "other"

    def _calculate_form_score(self, form_data: dict[str, Any]) -> int:
        """Calculate a score for form quality/relevance"""
        score = 0

        # Required fields present
        purposes = [f["purpose"] for f in form_data["fields"]]

        if "name" in purposes:
            score += 20
        if "email" in purposes:
            score += 25
        if "phone" in purposes:
            score += 20
        if "message" in purposes:
            score += 25
        if "service" in purposes:
            score += 10

        # Penalize too many fields (might be job application)
        if len(form_data["fields"]) > 10:
            score -= 20

        # Bonus for contact page URL
        if any(word in form_data["page_url"].lower() for word in ["contact", "quote", "estimate"]):
            score += 15

        return max(0, score)

    def _select_best_form(self, forms: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Select the best contact form from all found forms"""
        if not forms:
            return None

        # Sort by score
        sorted_forms = sorted(forms, key=lambda f: f["score"], reverse=True)

        # Return highest scoring form with minimum requirements
        for form in sorted_forms:
            purposes = [f["purpose"] for f in form["fields"]]
            if "email" in purposes or "phone" in purposes:
                return form

        # Return highest scoring form if no ideal form found
        return sorted_forms[0] if sorted_forms else None

    def fill_contact_form(self, contractor_lead: dict[str, Any], bid_card: dict[str, Any],
                         form_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Fill out a contact form on contractor website

        Args:
            contractor_lead: Contractor information
            bid_card: Project information
            form_info: Optional pre-analyzed form info

        Returns:
            Dict with submission results
        """
        try:
            # If no form info provided, analyze website first
            if not form_info:
                analysis = self.analyze_website_for_form(contractor_lead)
                if not analysis["success"] or not analysis["has_contact_form"]:
                    return {
                        "success": False,
                        "error": "No contact form found on website"
                    }
                form_info = analysis["best_form"]

            if not form_info:
                return {
                    "success": False,
                    "error": "No suitable contact form found"
                }

            self.start_browser()
            page = self.context.new_page()

            # Navigate to form page
            form_url = form_info["page_url"]
            print(f"[WFA] Navigating to form: {form_url}")
            page.goto(form_url, wait_until="networkidle", timeout=30000)

            # Wait a bit for dynamic content
            page.wait_for_timeout(2000)

            # Prepare form data
            form_data = self._prepare_form_data(contractor_lead, bid_card)

            # Fill form fields
            filled_fields = []
            form_selector = f'form:nth-of-type({form_info["form_index"] + 1})'

            for field in form_info["fields"]:
                try:
                    value = form_data.get(field["purpose"], "")
                    if not value:
                        continue

                    # Build selector
                    selector = self._build_field_selector(field, form_selector)

                    # Fill field based on type
                    if field["tag"] == "select":
                        # Handle select dropdown
                        page.select_option(selector, value)
                    elif field["type"] == "checkbox":
                        # Handle checkbox
                        page.check(selector)
                    elif field["type"] == "radio":
                        # Handle radio button
                        page.click(selector)
                    else:
                        # Text input or textarea
                        page.fill(selector, value)

                    filled_fields.append({
                        "purpose": field["purpose"],
                        "value": value[:50] + "..." if len(value) > 50 else value
                    })

                    # Small delay between fields to seem human
                    page.wait_for_timeout(500)

                except Exception as e:
                    print(f"[WFA] Error filling field {field['purpose']}: {e}")

            # Submit form
            submit_result = self._submit_form(page, form_selector)

            # Record attempt in database
            attempt_data = {
                "contractor_lead_id": contractor_lead["id"],
                "bid_card_id": bid_card["id"],
                "channel": "website_form",
                "form_url": form_url,
                "form_fields_filled": {
                    "fields": filled_fields,
                    "total_fields": len(form_info["fields"]),
                    "filled_count": len(filled_fields)
                },
                "form_submission_success": submit_result["success"],
                "form_error_message": submit_result.get("error"),
                "message_content": form_data.get("message", ""),
                "status": "form_filled" if submit_result["success"] else "failed"
            }

            self._record_outreach_attempt(attempt_data)

            page.close()

            return {
                "success": submit_result["success"],
                "form_url": form_url,
                "fields_filled": len(filled_fields),
                "submission_result": submit_result,
                "attempt_id": attempt_data.get("id")
            }

        except Exception as e:
            print(f"[WFA ERROR] Failed to fill form: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_form_data(self, contractor_lead: dict[str, Any], bid_card: dict[str, Any]) -> dict[str, str]:
        """Prepare data to fill into form"""
        bid_data = bid_card.get("bid_document", {}).get("all_extracted_data", {})

        # Generate professional message with bid card URL
        message = self._generate_contact_message(bid_data, bid_card)

        return {
            "name": "Sarah Johnson",  # Professional alias
            "email": "projects@instabids.com",
            "phone": "(407) 555-0199",  # Company phone
            "company": "Instabids Marketplace",
            "message": message,
            "address": bid_data.get("location", {}).get("full_location", ""),
            "city": bid_data.get("location", {}).get("city", ""),
            "state": bid_data.get("location", {}).get("state", ""),
            "zip": bid_data.get("location", {}).get("zip_code", ""),
            "service": bid_data.get("project_type", "home improvement"),
            "budget": self._format_budget_for_form(bid_data.get("budget_min"), bid_data.get("budget_max")),
            "timeline": bid_data.get("timeline", "As soon as possible")
        }

    def _generate_contact_message(self, bid_data: dict[str, Any], bid_card: dict[str, Any]) -> str:
        """Generate a professional contact message with bid card URL"""
        project_type = bid_data.get("project_type", "home improvement project")
        location = bid_data.get("location", {}).get("city", "our area")
        urgency = bid_data.get("urgency_level", "flexible")
        budget_min = bid_data.get("budget_min", 0)
        budget_max = bid_data.get("budget_max", 0)

        # Generate bid card URL
        bid_card_url = f"https://instabids.com/bid-cards/{bid_card['id']}"

        # Urgency-based opening
        if urgency == "emergency":
            opening = f"We have an urgent {project_type} in {location} that needs immediate attention."
        elif urgency == "week":
            opening = f"We're looking for a qualified contractor for a {project_type} in {location} to start within the next week."
        else:
            opening = f"We're seeking bids for a {project_type} in {location}."

        # Budget line
        if budget_min and budget_max:
            budget_line = f"The project budget is ${budget_min:,} - ${budget_max:,}."
        else:
            budget_line = "We're looking for competitive pricing."

        # Create message with bid card URL
        message = f"""{opening}

{budget_line}

We represent a homeowner who is ready to move forward with the right contractor. You can view complete project details, photos, and specifications here:

{bid_card_url}

The project includes:
{bid_data.get('project_description', 'Full details available at the link above.')}

We're contacting top-rated contractors in the area and would like to include you in our bidding process. Simply visit the link above to see if this project is a good fit for your expertise.

Best regards,
Sarah Johnson
Instabids Marketplace

P.S. This is a pre-qualified homeowner ready to start. You only pay our platform fee if you win the project."""

        return message

    def _format_budget_for_form(self, budget_min: int, budget_max: int) -> str:
        """Format budget for form field"""
        if budget_min and budget_max:
            return f"${budget_min:,} - ${budget_max:,}"
        elif budget_max:
            return f"Up to ${budget_max:,}"
        else:
            return "To be discussed"

    def _build_field_selector(self, field: dict[str, Any], form_selector: str) -> str:
        """Build CSS selector for form field"""
        if field["id"]:
            return f"#{field['id']}"
        elif field["name"]:
            tag = field["tag"]
            return f"{form_selector} {tag}[name='{field['name']}']"
        else:
            # Fallback to position
            tag = field["tag"]
            return f"{form_selector} {tag}:nth-of-type({field.get('index', 1)})"

    def _submit_form(self, page: Page, form_selector: str) -> dict[str, Any]:
        """Submit the form and handle response"""
        try:
            # Look for submit button
            submit_selectors = [
                f"{form_selector} button[type='submit']",
                f"{form_selector} input[type='submit']",
                f"{form_selector} button:has-text('Submit')",
                f"{form_selector} button:has-text('Send')",
                f"{form_selector} button:has-text('Contact')",
                f"{form_selector} input[value='Submit']"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = page.query_selector(selector)
                    if submit_button:
                        break
                except:
                    continue

            if not submit_button:
                return {
                    "success": False,
                    "error": "No submit button found"
                }

            # Click submit
            submit_button.click()

            # Wait for response
            page.wait_for_timeout(3000)

            # Check for success indicators
            success_patterns = [
                "thank you", "thanks", "success", "received",
                "we'll be in touch", "submitted", "confirmation"
            ]

            page_content = page.content().lower()

            for pattern in success_patterns:
                if pattern in page_content:
                    return {
                        "success": True,
                        "confirmation": pattern
                    }

            # Check if still on same page (might indicate error)
            if page.url == form_selector:
                # Look for error messages
                error_text = page.evaluate("""() => {
                    const errors = document.querySelectorAll('.error, .alert, [class*="error"], [role="alert"]');
                    return Array.from(errors).map(e => e.textContent).join(' ');
                }""")

                if error_text:
                    return {
                        "success": False,
                        "error": error_text[:200]
                    }

            # Assume success if navigated away
            return {
                "success": True,
                "confirmation": "Form submitted"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute"""
        if not url:
            return base_url

        if url.startswith(("http://", "https://")):
            return url

        if url.startswith("/"):
            # Absolute path
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        else:
            # Relative path
            if base_url.endswith("/"):
                return base_url + url
            else:
                return base_url + "/" + url

    def _update_contractor_lead_form_info(self, lead_id: str, form_analysis: dict[str, Any]):
        """Update contractor_lead with form information"""
        try:
            update_data = {
                "has_contact_form": form_analysis["has_contact_form"],
                "contact_form_url": form_analysis.get("best_form", {}).get("page_url"),
                "form_fields": form_analysis.get("best_form", {}).get("fields", []),
                "updated_at": datetime.now().isoformat()
            }

            self.supabase.table("contractor_leads").update(update_data).eq("id", lead_id).execute()

        except Exception as e:
            print(f"[WFA ERROR] Failed to update contractor lead: {e}")

    def _record_outreach_attempt(self, attempt_data: dict[str, Any]):
        """Record outreach attempt in database"""
        try:
            result = self.supabase.table("contractor_outreach_attempts").insert(attempt_data).execute()
            attempt_data["id"] = result.data[0]["id"] if result.data else None

            # Update engagement summary
            self._update_engagement_summary(attempt_data["contractor_lead_id"])

        except Exception as e:
            print(f"[WFA ERROR] Failed to record outreach attempt: {e}")

    def _update_engagement_summary(self, contractor_lead_id: str):
        """Update or create engagement summary"""
        try:
            # Check if summary exists
            result = self.supabase.table("contractor_engagement_summary").select("*").eq(
                "contractor_lead_id", contractor_lead_id
            ).execute()

            if result.data:
                # Update existing
                update_data = {
                    "website_form_count": result.data[0]["website_form_count"] + 1,
                    "total_outreach_count": result.data[0]["total_outreach_count"] + 1,
                    "last_contacted_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                self.supabase.table("contractor_engagement_summary").update(update_data).eq(
                    "contractor_lead_id", contractor_lead_id
                ).execute()
            else:
                # Create new
                insert_data = {
                    "contractor_lead_id": contractor_lead_id,
                    "website_form_count": 1,
                    "total_outreach_count": 1,
                    "first_contacted_at": datetime.now().isoformat(),
                    "last_contacted_at": datetime.now().isoformat()
                }

                self.supabase.table("contractor_engagement_summary").insert(insert_data).execute()

        except Exception as e:
            print(f"[WFA ERROR] Failed to update engagement summary: {e}")

    def batch_fill_forms(self, contractor_leads: list[dict[str, Any]], bid_card: dict[str, Any],
                        max_attempts: int = 10) -> dict[str, Any]:
        """
        Fill forms for multiple contractors

        Args:
            contractor_leads: List of contractors to contact
            bid_card: Project information
            max_attempts: Maximum forms to fill

        Returns:
            Summary of results
        """
        results = {
            "total_attempted": 0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "no_form_found": 0,
            "details": []
        }

        try:
            self.start_browser()

            for i, contractor in enumerate(contractor_leads[:max_attempts]):
                print(f"\n[WFA] Processing contractor {i+1}/{min(len(contractor_leads), max_attempts)}: {contractor.get('company_name')}")

                # Skip if no website
                if not contractor.get("website"):
                    results["no_form_found"] += 1
                    results["details"].append({
                        "contractor_id": contractor["id"],
                        "company_name": contractor["company_name"],
                        "success": False,
                        "reason": "No website"
                    })
                    continue

                results["total_attempted"] += 1

                # Fill form
                result = self.fill_contact_form(contractor, bid_card)

                if result["success"]:
                    results["successful_submissions"] += 1
                else:
                    if "No contact form found" in result.get("error", ""):
                        results["no_form_found"] += 1
                    else:
                        results["failed_submissions"] += 1

                results["details"].append({
                    "contractor_id": contractor["id"],
                    "company_name": contractor["company_name"],
                    "success": result["success"],
                    "form_url": result.get("form_url"),
                    "error": result.get("error")
                })

                # Delay between attempts
                if i < len(contractor_leads) - 1:
                    time.sleep(5)

        finally:
            self.stop_browser()

        print(f"\n[WFA] Batch complete: {results['successful_submissions']}/{results['total_attempted']} successful")
        return results


# Test the agent
if __name__ == "__main__":
    wfa = WebsiteFormAutomationAgent()

    # Test contractor
    test_contractor = {
        "id": "test-123",
        "company_name": "Test Contractor Inc",
        "website": "https://example.com"
    }

    # Test bid card
    test_bid_card = {
        "id": "bid-123",
        "bid_document": {
            "all_extracted_data": {
                "project_type": "kitchen remodel",
                "location": {
                    "city": "Orlando",
                    "state": "FL",
                    "zip_code": "32801"
                },
                "budget_min": 25000,
                "budget_max": 35000,
                "urgency_level": "week"
            }
        }
    }

    # Test form analysis
    print("Testing WFA agent...")
    result = wfa.analyze_website_for_form(test_contractor)
    print(f"Analysis result: {json.dumps(result, indent=2)}")

    wfa.stop_browser()
