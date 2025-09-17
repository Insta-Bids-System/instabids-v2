"""
Claude-Enhanced WFA (Website Form Automation Agent)
Uses Claude Opus 4 to intelligently understand and fill any website form
"""
import asyncio
import json
import os
import re
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI
from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright
from supabase import create_client


class WebsiteFormAutomationAgent:
    """WFA with Claude intelligence for understanding any form"""

    def __init__(self):
        """Initialize WFA with Claude"""
        load_dotenv(override=True)

        # Database
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

        # Claude
        self.anthropic_api_key = os.getenv("OPENAI_API_KEY")
        self.claude = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Browser settings
        self.browser = None
        self.context = None
        self.headless = os.getenv("WFA_HEADLESS", "true").lower() == "true"

        print("[WFA+Claude] Initialized with Claude Opus 4 intelligence")

    def start_browser(self):
        """Start browser"""
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
            print("[WFA+Claude] Browser started")

    def analyze_form_with_claude(self, page: Page, html_content: str) -> dict[str, Any]:
        """Use Claude to understand the form structure and fields"""

        prompt = f"""Analyze this HTML form and identify all form fields and their purposes.

HTML CONTENT:
{html_content[:3000]}  # Limit to avoid token limits

TASK:
1. Identify all input fields, textareas, and selects
2. Determine the purpose of each field (name, email, phone, message, etc.)
3. Identify which fields are required
4. Find the submit button
5. Understand any special requirements or validation

Return a JSON structure like this:
{{
    "form_analysis": {{
        "has_contact_form": true/false,
        "form_purpose": "contact form/quote request/etc",
        "fields": [
            {{
                "selector": "CSS selector or ID",
                "type": "text/email/tel/textarea/select",
                "purpose": "name/email/phone/message/company/etc",
                "label": "visible label text",
                "required": true/false,
                "validation": "any validation rules"
            }}
        ],
        "submit_button": {{
            "selector": "CSS selector",
            "text": "button text"
        }},
        "special_notes": "any special handling needed"
    }}
}}"""

        try:
            response = self.claude.messages.create(
                model="gpt-4",
                max_tokens=1500,
                temperature=0,  # Deterministic for analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            claude_response = response.choices[0].message.content

            # Extract JSON from response
            import json
            json_match = re.search(r"\{[\s\S]*\}", claude_response)
            if json_match:
                analysis = json.loads(json_match.group())
                print("[Claude] Successfully analyzed form structure")
                return analysis
            else:
                print("[Claude] Could not parse form analysis")
                return {"form_analysis": {"has_contact_form": False}}

        except Exception as e:
            print(f"[Claude ERROR] Form analysis failed: {e}")
            return {"form_analysis": {"has_contact_form": False}}

    def create_form_filling_strategy(self,
                                   form_analysis: dict[str, Any],
                                   bid_card_data: dict[str, Any]) -> dict[str, Any]:
        """Use Claude to create a strategy for filling the form"""

        fields = form_analysis.get("form_analysis", {}).get("fields", [])

        # Extract bid card details
        project_type = bid_card_data.get("project_type", "home improvement").replace("_", " ").title()
        budget_min = bid_card_data.get("budget_min", 0)
        budget_max = bid_card_data.get("budget_max", 0)
        budget = f"${budget_min:,} - ${budget_max:,}" if budget_min > 0 else "Flexible"
        timeline = bid_card_data.get("timeline", "Flexible timeline")
        location = bid_card_data.get("location", "Location not specified")
        scope = bid_card_data.get("scope_details", "Full details available on platform")
        homeowner_name = bid_card_data.get("homeowner", {}).get("name", "Homeowner")

        prompt = f"""Create a form filling strategy for this contractor contact form.

FORM FIELDS:
{json.dumps(fields, indent=2)}

PROJECT DETAILS:
- Type: {project_type}
- Budget: {budget}
- Timeline: {timeline}
- Location: {location}
- Scope: {scope}
- Homeowner: {homeowner_name}

INSTABIDS VALUE PROPOSITION:
- Pre-qualified homeowners ready to start
- All project details verified upfront
- Direct connection to serious buyers
- No tire kickers or price shoppers
- Projects match contractor's expertise

Create a strategy for filling each field. Make the message compelling and highlight why this is a premium opportunity through InstaBids.

Return JSON like:
{{
    "field_values": {{
        "field_selector": "value to enter",
        ...
    }},
    "message_strategy": "approach for the main message",
    "emphasis_points": ["key points to highlight"]
}}"""

        try:
            response = self.claude.messages.create(
                model="gpt-4",
                max_tokens=1000,
                temperature=0.7,  # Some creativity for messaging
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            claude_response = response.choices[0].message.content
            json_match = re.search(r"\{[\s\S]*\}", claude_response)

            if json_match:
                strategy = json.loads(json_match.group())
                print("[Claude] Created personalized form filling strategy")
                return strategy
            else:
                # Fallback strategy
                return self._create_fallback_strategy(fields, bid_card_data)

        except Exception as e:
            print(f"[Claude ERROR] Strategy creation failed: {e}")
            return self._create_fallback_strategy(fields, bid_card_data)

    def fill_contact_form(self, contractor: dict[str, Any], bid_card: dict[str, Any]) -> dict[str, Any]:
        """Fill contractor's contact form using Claude intelligence"""
        try:
            website = contractor.get("website", "")
            if not website:
                return {"success": False, "error": "No website provided"}

            # Ensure browser is started
            self.start_browser()
            page = self.context.new_page()

            print(f"[WFA+Claude] Navigating to {website}")

            # Navigate to website
            try:
                page.goto(website, wait_until="networkidle", timeout=30000)
                # Let page fully load - using page wait instead of blocking sleep
                page.wait_for_timeout(2000)
            except:
                # Try adding https if missing
                if not website.startswith(("http://", "https://")):
                    website = f"https://{website}"
                    page.goto(website, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)

            # Get page HTML for Claude
            html_content = page.content()

            # Use Claude to analyze the form
            print("[WFA+Claude] Asking Claude to analyze form...")
            form_analysis = self.analyze_form_with_claude(page, html_content)

            if not form_analysis.get("form_analysis", {}).get("has_contact_form"):
                # Try to find contact page
                print("[WFA+Claude] No form on homepage, looking for contact page...")
                contact_link = self._find_contact_page(page)

                if contact_link:
                    page.click(contact_link)
                    page.wait_for_timeout(2000)
                    html_content = page.content()
                    form_analysis = self.analyze_form_with_claude(page, html_content)

            if not form_analysis.get("form_analysis", {}).get("has_contact_form"):
                return {
                    "success": False,
                    "error": "No contact form found",
                    "website": website
                }

            # Create filling strategy with Claude
            print("[WFA+Claude] Creating personalized filling strategy...")
            strategy = self.create_form_filling_strategy(form_analysis, bid_card)

            # Fill the form using Claude's strategy
            print("[WFA+Claude] Filling form with Claude's strategy...")
            fill_result = self._execute_form_filling(page, form_analysis, strategy)

            if fill_result["success"]:
                # Track submission
                submission_id = str(uuid.uuid4())
                self._track_form_submission(submission_id, contractor, bid_card, strategy)

                print(f"[WFA+Claude] Successfully filled form for {contractor.get('company_name')}")
                return {
                    "success": True,
                    "submission_id": submission_id,
                    "website": website,
                    "claude_analyzed": True,
                    "fields_filled": len(strategy.get("field_values", {}))
                }
            else:
                return fill_result

        except Exception as e:
            print(f"[WFA+Claude ERROR] Form filling failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if "page" in locals():
                page.close()

    def _execute_form_filling(self, page: Page, form_analysis: dict[str, Any],
                            strategy: dict[str, Any]) -> dict[str, Any]:
        """Execute the form filling based on Claude's strategy"""
        try:
            fields = form_analysis.get("form_analysis", {}).get("fields", [])
            field_values = strategy.get("field_values", {})

            # Fill each field
            for field in fields:
                selector = field.get("selector")
                if not selector:
                    continue

                value = field_values.get(selector, "")
                if not value:
                    # Try to find value by purpose
                    purpose = field.get("purpose", "")
                    for sel, val in field_values.items():
                        if purpose in sel or purpose in str(val):
                            value = val
                            break

                if value:
                    try:
                        # Type with human-like delays
                        page.fill(selector, str(value))
                        page.wait_for_timeout(500)  # Small delay between fields
                    except:
                        # Try clicking first then typing
                        try:
                            page.click(selector)
                            page.type(selector, str(value), delay=50)  # Type like human
                        except:
                            print(f"[WFA+Claude] Could not fill field: {selector}")

            # Submit form
            submit_btn = form_analysis.get("form_analysis", {}).get("submit_button", {})
            if submit_btn.get("selector"):
                page.wait_for_timeout(1000)  # Pause before submit
                page.click(submit_btn["selector"])
                page.wait_for_timeout(3000)  # Wait for submission

                return {"success": True}
            else:
                return {"success": False, "error": "No submit button found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _find_contact_page(self, page: Page) -> Optional[str]:
        """Find contact page link"""
        contact_patterns = ["contact", "get in touch", "reach us", "quote", "estimate"]

        for pattern in contact_patterns:
            try:
                link = page.locator(f'a:has-text("{pattern}")').first
                if link.count() > 0:
                    return link
            except:
                pass

        return None

    def _create_fallback_strategy(self, fields: list[dict], bid_card_data: dict[str, Any]) -> dict[str, Any]:
        """Fallback strategy if Claude fails"""
        return {
            "field_values": {
                "name": bid_card_data.get("homeowner", {}).get("name", "InstaBids User"),
                "email": "projects@instabids.com",
                "phone": "(888) 555-0123",
                "message": f"New {bid_card_data.get('project_type', 'project')} opportunity via InstaBids"
            }
        }

    def _track_form_submission(self, submission_id: str, contractor: dict[str, Any],
                             bid_card: dict[str, Any], strategy: dict[str, Any]):
        """Track form submission in database"""
        try:
            self.supabase.table("wfa_form_submissions").insert({
                "id": submission_id,
                "contractor_id": contractor.get("id"),
                "bid_card_id": bid_card.get("id"),
                "website": contractor.get("website"),
                "form_filled_at": datetime.now().isoformat(),
                "claude_strategy": strategy,
                "status": "submitted"
            }).execute()
        except Exception as e:
            print(f"[WFA+Claude] Failed to track submission: {e}")

    def stop_browser(self):
        """Stop browser"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.context = None
