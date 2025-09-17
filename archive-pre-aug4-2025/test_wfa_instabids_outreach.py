"""
Test WFA: Instabids reaches out to contractors with bid card links
This shows the REAL flow - Instabids fills contractor forms with our pitch
"""

def test_instabids_contractor_outreach():
    """Test Instabids filling out contractor forms with bid card links"""
    print("=" * 60)
    print("INSTABIDS CONTRACTOR OUTREACH TEST")
    print("=" * 60)
    print("Testing: WFA fills contractor forms AS Instabids with bid card links")
    print()

    # Instabids company information for outreach
    instabids_info = {
        "company_name": "Instabids",
        "contact_name": "Sales Team",
        "email": "partnerships@instabids.com",
        "phone": "(555) 123-BIDS",
        "website": "https://instabids.com",
        "opportunity_type": "lead_generation"
    }

    # Our sales pitch with rich bid card preview link
    bid_card_id = "d57cd6cd-f424-460e-9c15-7a08c09507f3"
    bid_card_preview_url = f"http://localhost:8008/api/bid-cards/{bid_card_id}/preview"

    sales_pitch = f"""🚀 STOP PAYING FOR LEADS!

We're Instabids - the AI-powered platform DESTROYING Angie's List and Google's lead monopoly.

❌ No more $50-200 per lead
❌ No more competing with 10+ contractors
❌ No more fake leads

✅ FREE qualified projects in your area
✅ Direct homeowner communication
✅ Only pay when you WIN the job

HERE'S A REAL PROJECT YOU CAN BID ON RIGHT NOW:
{bid_card_preview_url}

This is a {get_project_summary(bid_card_id)} - see the full details above.

💡 CLICK THE LINK ABOVE - It shows a beautiful visual preview with project details, budget, timeline, and location. This is exactly what you'll see when shared in emails, SMS, and social media!

Ready to cut your customer acquisition costs by 90%?

Reply to get early access to Instabids Pro."""

    return {
        "contractor_website": "Green Lawn Pro (Orlando)",
        "instabids_info": instabids_info,
        "sales_pitch": sales_pitch,
        "bid_card_link": f"http://localhost:8008/api/bid-cards/{bid_card_id}",
        "bid_card_preview_url": bid_card_preview_url,
        "expected_outcome": "Contractor sees rich visual preview, clicks link, signs up"
    }

def get_project_summary(bid_card_id):
    """Get a quick project summary for the pitch"""
    try:
        import requests
        response = requests.get(f"http://localhost:8008/api/bid-cards/{bid_card_id}")
        if response.status_code == 200:
            data = response.json()
            project = data.get("project_type", "").replace("_", " ")
            budget = data.get("budget_display", "")
            location = data.get("location", {}).get("city", "")
            return f"{project} project ({budget}) in {location}"
    except:
        pass
    return "lawn care project"

def simulate_wfa_form_fill():
    """Simulate WFA filling out the contractor form"""
    print("🤖 WFA SIMULATION:")
    print("1. Navigate to Green Lawn Pro website")
    print("2. Find business opportunity form")
    print("3. Fill out form AS INSTABIDS:")

    test_data = test_instabids_contractor_outreach()

    print(f"   Company: {test_data['instabids_info']['company_name']}")
    print(f"   Contact: {test_data['instabids_info']['contact_name']}")
    print(f"   Email: {test_data['instabids_info']['email']}")
    print(f"   Phone: {test_data['instabids_info']['phone']}")
    print(f"   Website: {test_data['instabids_info']['website']}")
    print("   Message:")
    print("   " + "\\n   ".join(test_data["sales_pitch"].split("\\n")[:5]))
    print("   [... includes bid card link ...]")
    print()
    print("4. Submit form")
    print("5. Scrape contractor contact info during submission")
    print()

    return test_data

def main():
    """Run the WFA outreach test"""
    test_data = simulate_wfa_form_fill()

    print("🎯 EXPECTED CONTRACTOR EXPERIENCE:")
    print("1. Receives form submission notification")
    print("2. Sees Instabids pitch about free leads")
    print("3. Clicks bid card link:")
    print(f"   {test_data['bid_card_link']}")
    print("4. Views real project details")
    print("5. Signs up for Instabids account to bid")
    print()

    print("📊 TRACKING REQUIREMENTS:")
    print("- Log: Form submitted to Green Lawn Pro")
    print("- Status: Awaiting contractor response")
    print("- Next: Send follow-up email in 24 hours")
    print("- Contact info scraped: Yes")
    print()

    print("✅ TEST READY FOR BROWSER AUTOMATION")
    print("Run this test in browser to see actual form filling")

    return test_data

if __name__ == "__main__":
    main()
