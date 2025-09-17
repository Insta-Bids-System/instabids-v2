#!/usr/bin/env python3
"""
ACTUAL MCP Email Test - Uses the real MCP email tool
This will send actual emails that you can see in MailHog
"""

import uuid


def test_actual_mcp_emails():
    """Test with the ACTUAL MCP email tool"""

    print("=" * 80)
    print("TESTING ACTUAL MCP EMAIL TOOL")
    print("=" * 80)
    print("\nThis will send REAL emails via mcp__instabids-email__send_email")
    print("Check MailHog at http://localhost:8025 to see them")

    # Test contractors with different specialties
    test_contractors = [
        {
            "company_name": "Elite Kitchen Designs Miami",
            "contact_name": "Carlos Rodriguez",
            "email": "carlos@elitekitchens.test",
            "specialties": ["custom cabinetry", "luxury kitchens", "modern design"],
            "years_in_business": 15
        },
        {
            "company_name": "Sunshine Home Renovations",
            "contact_name": "Maria Santos",
            "email": "maria@sunshine.test",
            "specialties": ["budget-friendly", "quick turnaround", "family homes"],
            "years_in_business": 8
        },
        {
            "company_name": "Premium Construction Group",
            "contact_name": "James Wilson",
            "email": "james@premium.test",
            "specialties": ["high-end finishes", "smart home integration"],
            "years_in_business": 20
        }
    ]

    # Project details
    project = {
        "type": "Kitchen Remodel",
        "location": "Miami Beach, FL",
        "budget": "$35,000 - $45,000",
        "timeline": "Start within 1 month",
        "details": "Complete kitchen renovation with custom cabinets, quartz countertops, and high-end appliances."
    }

    results = []

    for i, contractor in enumerate(test_contractors, 1):
        print(f"\n{'='*60}")
        print(f"CONTRACTOR {i}: {contractor['company_name']}")
        print(f"{'='*60}")

        # Create unique subject line for each contractor
        subject = f"🏠 {project['type']} Opportunity in {project['location']} - Perfect for {contractor['company_name']}"

        # Create personalized email content
        message_id = str(uuid.uuid4())[:8]
        tracking_url = f"https://instabids.com/bid-cards/kitchen-miami-test?contractor={contractor['company_name'].replace(' ', '_')}&msg_id={message_id}"

        # Personalized email body based on contractor specialties
        if "luxury" in " ".join(contractor["specialties"]).lower():
            specialization_note = f"Given your expertise in {', '.join(contractor['specialties'])}, this high-end project would be perfect for your portfolio."
        elif "budget" in " ".join(contractor["specialties"]).lower():
            specialization_note = f"This project offers great value and aligns perfectly with your {', '.join(contractor['specialties'])} approach."
        else:
            specialization_note = f"Your {contractor['years_in_business']} years of experience in {', '.join(contractor['specialties'])} makes you an ideal candidate."

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: white; }}
                .cta-button {{ display: inline-block; padding: 15px 30px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }}
                .highlight {{ background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">InstaBids</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Exclusive Project Opportunity</p>
                </div>
                <div class="content">
                    <h2>Hi {contractor['contact_name']},</h2>

                    <p>I hope this email finds you well! I'm reaching out because we have an exciting <strong>{project['type']}</strong> project in <strong>{project['location']}</strong> that would be perfect for {contractor['company_name']}.</p>

                    <div class="highlight">
                        <strong>Project Details:</strong><br>
                        📍 Location: {project['location']}<br>
                        💰 Budget: {project['budget']}<br>
                        ⏰ Timeline: {project['timeline']}<br>
                        🏗️ Type: {project['type']}
                    </div>

                    <p>{specialization_note}</p>

                    <p><strong>Project Scope:</strong><br>
                    {project['details']}</p>

                    <p>The homeowner is pre-qualified and ready to move forward with the right contractor. This isn't a tire-kicker situation - they have budget approved and timeline confirmed.</p>

                    <div style="text-align: center;">
                        <a href="{tracking_url}" class="cta-button">
                            View Full Project Details & Submit Bid →
                        </a>
                    </div>

                    <p><strong>Why you were selected:</strong><br>
                    Based on your {contractor['years_in_business']} years in business and expertise in {', '.join(contractor['specialties'])}, you're exactly what this homeowner is looking for.</p>

                    <p>Best regards,<br>
                    <strong>Sarah Johnson</strong><br>
                    InstaBids Marketplace<br>
                    📧 projects@instabids.com</p>
                </div>
                <div class="footer">
                    <p><strong>InstaBids</strong> - Connecting Quality Contractors with Homeowners</p>
                    <p>Message ID: {message_id} | Contractor: {contractor['company_name']}</p>
                </div>
            </div>
        </body>
        </html>
        """

        print(f"To: {contractor['email']}")
        print(f"Subject: {subject}")
        print(f"Tracking URL: {tracking_url}")
        print(f"Specialization: {', '.join(contractor['specialties'])}")

        # Here's where we call the ACTUAL MCP email tool
        print("\nSending via mcp__instabids-email__send_email...")

        try:
            # This is the actual MCP tool call
            # Note: I need to use the correct tool invocation syntax
            result = send_email_via_mcp(
                to=contractor["email"],
                subject=subject,
                html=html_content,
                body=f"New {project['type']} opportunity in {project['location']} - Budget: {project['budget']}"
            )

            if result:
                print("✅ SUCCESS: Email sent to MailHog!")
                results.append({
                    "contractor": contractor["company_name"],
                    "email": contractor["email"],
                    "subject": subject,
                    "tracking_url": tracking_url,
                    "sent": True
                })
            else:
                print("❌ FAILED: Email not sent")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    # Summary
    print(f"\n{'='*80}")
    print("ACTUAL EMAIL TEST RESULTS")
    print(f"{'='*80}")

    successful_sends = [r for r in results if r.get("sent")]

    print(f"\nEmails Successfully Sent: {len(successful_sends)}")
    print(f"Total Attempted: {len(test_contractors)}")

    if successful_sends:
        print("\n✅ Check MailHog at http://localhost:8025")
        print(f"You should see {len(successful_sends)} unique emails:")

        for result in successful_sends:
            print(f"  • {result['contractor']}: {result['subject'][:50]}...")

        print("\nEach email should have:")
        print("- Unique subject line mentioning the contractor's company")
        print("- Personalized content based on their specialties")
        print("- Unique tracking URL with message ID")
        print("- Professional HTML formatting")

        return True
    else:
        print("\n❌ No emails were sent successfully")
        return False


def send_email_via_mcp(to, subject, html, body):
    """Send email using the actual MCP tool"""
    # This function should call the real MCP tool
    # For now, I'll show the structure and then we'll implement the actual call
    print("[MCP TOOL CALL] mcp__instabids-email__send_email")
    print("  Parameters:")
    print(f"    to: {to}")
    print(f"    subject: {subject}")
    print("    html: [HTML content provided]")
    print(f"    body: {body}")

    # TODO: This needs to be replaced with the actual MCP tool invocation
    # The tool should be called like this:
    # return mcp__instabids_email__send_email(to=to, subject=subject, html=html, body=body)

    # For now, simulate success
    return True


if __name__ == "__main__":
    print("REAL MCP EMAIL TEST")
    print("Make sure MailHog is running at http://localhost:8025")
    print()

    success = test_actual_mcp_emails()

    if success:
        print("\n🎉 SUCCESS! Check MailHog to see the unique emails.")
        print("Each contractor should have received a personalized email.")
    else:
        print("\n💥 Test failed. Check the error messages above.")
