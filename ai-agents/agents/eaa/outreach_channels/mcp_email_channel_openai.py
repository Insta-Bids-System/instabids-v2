"""
MCP Email Channel with OpenAI Integration
Uses GPT-4 to write personalized emails for each contractor
"""
import os
import uuid
from datetime import datetime
from typing import Any

from openai import OpenAI
from dotenv import load_dotenv


class MCPEmailChannelWithOpenAI:
    """Email channel that uses OpenAI to write personalized emails"""

    def __init__(self):
        """Initialize with OpenAI client"""
        # Load environment variables
        load_dotenv(override=True)

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("[MCPEmailChannel+OpenAI ERROR] OPENAI_API_KEY not found in environment!")
        else:
            print(f"[MCPEmailChannel+OpenAI] Found API key: {self.openai_api_key[:10]}...")

        self.client = OpenAI(api_key=self.openai_api_key)
        self.sent_emails = []  # For testing verification
        print("[MCPEmailChannel+OpenAI] Initialized with GPT-4 integration")

    def send_personalized_outreach(self,
                                 contractor: dict[str, Any],
                                 bid_card_data: dict[str, Any],
                                 campaign_id: str) -> dict[str, Any]:
        """Send personalized email using OpenAI to write content"""
        try:
            message_id = str(uuid.uuid4())[:8]

            # Use OpenAI to create personalized email
            email_data = self._create_openai_personalized_email(
                contractor, bid_card_data, message_id, campaign_id
            )

            # Get contractor email
            contractor_email = contractor.get("email", "contractor@example.com")

            # Send via MCP
            result = self._send_via_mcp(
                contractor_email, email_data, message_id, campaign_id
            )

            print(f"[MCPEmailChannel+OpenAI] Sent OpenAI-written email to {contractor.get('company_name')}")
            return result

        except Exception as e:
            print(f"[MCPEmailChannel+OpenAI ERROR] Failed: {e}")
            return {"success": False, "error": str(e)}

    def _create_openai_personalized_email(self,
                                        contractor: dict[str, Any],
                                        bid_card_data: dict[str, Any],
                                        message_id: str,
                                        campaign_id: str) -> dict[str, Any]:
        """Use OpenAI to write a unique, personalized email"""

        # Extract contractor details
        company_name = contractor.get("company_name", "Contractor")
        contact_name = contractor.get("contact_name", "there")
        contractor_services = contractor.get("service_types", [])
        contractor_specialties = contractor.get("specialties", [])
        years_in_business = contractor.get("years_in_business", "several")

        # Extract project details
        project_type = bid_card_data.get("project_type", "home improvement").replace("_", " ").title()
        location = bid_card_data.get("location", "your area")
        budget_min = bid_card_data.get("budget_min", 0)
        budget_max = bid_card_data.get("budget_max", 0)
        budget_range = f"${budget_min:,} - ${budget_max:,}" if budget_min > 0 else "Flexible budget"
        timeline = bid_card_data.get("timeline", "Flexible timeline")
        scope_details = bid_card_data.get("scope_details", "Full project details available on the platform")
        urgency = bid_card_data.get("urgency_level", "standard")

        # Create external URL with tracking
        base_url = bid_card_data.get("external_url", "https://instabids.com/bid-cards/default")
        external_url = f"{base_url}?source=email&contractor={company_name.replace(' ', '_')}&msg_id={message_id}&campaign={campaign_id}"

        # Create prompt for OpenAI
        prompt = f"""Write a personalized email to a contractor about a project opportunity. Make it compelling and unique.

CONTRACTOR INFORMATION:
- Company: {company_name}
- Contact: {contact_name}
- Services: {', '.join(contractor_services) if contractor_services else 'General contracting'}
- Specialties: {', '.join(contractor_specialties) if contractor_specialties else 'Various'}
- Years in business: {years_in_business}

PROJECT DETAILS:
- Type: {project_type}
- Location: {location}
- Budget: {budget_range}
- Timeline: {timeline}
- Urgency: {urgency}
- Scope: {scope_details}

REQUIREMENTS:
1. Write a compelling subject line that mentions the project type and location
2. Start with a personalized greeting using the contact name
3. Reference something specific about their company (services, specialties, or experience)
4. Describe why this project is a good fit for them specifically
5. Include the project details naturally in the email
6. Create urgency if it's an urgent project
7. End with a clear call-to-action to view the project and submit a bid

IMPORTANT:
- Keep it professional but conversational
- Make it feel like a personal opportunity, not a mass email
- Highlight why they were specifically selected
- Don't use generic templates or obvious placeholders
- Include this exact link for the CTA: {external_url}

Return the email in this format:
SUBJECT: [your subject line here]
BODY: [your email body here]"""

        # Call OpenAI API
        try:
            response = self.client.messages.create(
                model="gpt-4-turbo-preview",
                max_tokens=1000,
                temperature=0.9,  # Higher temperature for more variety
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse OpenAI's response
            openai_response = response.choices[0].message.content

            # Extract subject and body
            lines = openai_response.strip().split("\n")
            subject = ""
            body = ""

            parsing_body = False
            for line in lines:
                if line.startswith("SUBJECT:"):
                    subject = line.replace("SUBJECT:", "").strip()
                elif line.startswith("BODY:"):
                    body = line.replace("BODY:", "").strip()
                    parsing_body = True
                elif parsing_body:
                    body += "\n" + line

            # Clean up body
            body = body.strip()

            # Convert to HTML with styling
            html_body = self._convert_to_html(body, external_url, company_name, contractor.get("email", ""))

            print(f"[OpenAI] Generated unique email for {company_name}")
            print(f"  Subject: {subject}")

            return {
                "subject": subject,
                "html_content": html_body,
                "plain_text": body,
                "company_personalization": {
                    "company_name": company_name,
                    "contact_name": contact_name,
                    "project_type": project_type,
                    "location": location,
                    "budget_range": budget_range,
                    "external_url": external_url,
                    "message_id": message_id,
                    "openai_generated": True
                }
            }

        except Exception as e:
            print(f"[OpenAI ERROR] Failed to generate email: {e}")
            # Fallback to template if OpenAI fails
            return self._create_fallback_email(contractor, bid_card_data, message_id, campaign_id)

    def _convert_to_html(self, plain_text: str, cta_url: str, company_name: str, contractor_email: str) -> str:
        """Convert OpenAI's plain text to styled HTML"""

        # Convert line breaks to paragraphs
        paragraphs = plain_text.split("\n\n")
        html_body = ""

        for para in paragraphs:
            if para.strip():
                # Check if it's the CTA paragraph (contains the URL)
                if cta_url in para:
                    # Extract the CTA text and create button
                    cta_text = para.replace(cta_url, "").strip()
                    html_body += f"""
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{cta_url}" style="display: inline-block; padding: 15px 30px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            {cta_text if cta_text else 'View Project & Submit Bid'} →
                        </a>
                    </div>
                    """
                else:
                    html_body += f"<p style='margin: 15px 0; line-height: 1.6;'>{para}</p>"

        # Wrap in full HTML template
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">InstaBids</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Exclusive Project Opportunity</p>
                </div>
                <div class="content">
                    {html_body}
                </div>
                <div class="footer">
                    <p><strong>InstaBids</strong> - Connecting Quality Contractors with Homeowners</p>
                    <p>This email was sent to {contractor_email} | Company: {company_name}</p>
                    <p>Message ID: {cta_url.split('msg_id=')[1].split('&')[0] if 'msg_id=' in cta_url else 'unknown'}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return full_html

    def _create_fallback_email(self, contractor: dict[str, Any], bid_card_data: dict[str, Any], message_id: str, campaign_id: str) -> dict[str, Any]:
        """Fallback template if OpenAI fails"""
        # Similar to original template
        company_name = contractor.get("company_name", "Contractor")
        project_type = bid_card_data.get("project_type", "project").replace("_", " ").title()
        location = bid_card_data.get("location", "your area")

        # Create external URL with tracking
        base_url = bid_card_data.get("external_url", "https://instabids.com/bid-cards/default")
        external_url = f"{base_url}?source=email&contractor={company_name.replace(' ', '_')}&msg_id={message_id}&campaign={campaign_id}"

        subject = f"New {project_type} Opportunity in {location} - Perfect for {company_name}"

        return {
            "subject": subject,
            "html_content": f"<p>We have a new {project_type} project in {location}...</p>",
            "plain_text": f"We have a new {project_type} project in {location}...",
            "company_personalization": {
                "company_name": company_name,
                "message_id": message_id,
                "external_url": external_url,
                "openai_generated": False
            }
        }

    def _send_via_mcp(self, to_email: str, email_data: dict[str, Any],
                     message_id: str, campaign_id: str) -> dict[str, Any]:
        """Send email via MCP tool (placeholder for actual MCP integration)"""
        try:
            print("[MCP] Would send email via mcp__instabids-email__send_email")
            print(f"  To: {to_email}")
            print(f"  Subject: {email_data['subject']}")

            # Store for verification
            self._store_sent_email(to_email, email_data, message_id, campaign_id)

            return {
                "success": True,
                "message_id": message_id,
                "mcp_tool": "mcp__instabids-email__send_email",
                "openai_generated": email_data["company_personalization"].get("openai_generated", False),
                "unique_elements": {
                    "company_name": email_data["company_personalization"]["company_name"],
                    "external_url": email_data["company_personalization"]["external_url"],
                    "message_id": message_id
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _store_sent_email(self, to_email: str, email_data: dict[str, Any],
                         message_id: str, campaign_id: str):
        """Store sent email for testing verification"""
        self.sent_emails.append({
            "to": to_email,
            "subject": email_data["subject"],
            "company_name": email_data["company_personalization"]["company_name"],
            "message_id": message_id,
            "campaign_id": campaign_id,
            "external_url": email_data["company_personalization"]["external_url"],
            "sent_at": datetime.now().isoformat(),
            "openai_generated": email_data["company_personalization"].get("openai_generated", False)
        })

    def get_sent_emails_for_testing(self) -> list[dict[str, Any]]:
        """Get all sent emails for verification"""
        return self.sent_emails
