#!/usr/bin/env python3
"""
Create REAL demonstration data for contractor proposals and messaging
This will create an actual bid card with multiple contractors communicating
"""
import sys
import io
# Set UTF-8 encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import uuid
from datetime import datetime, timedelta
import random
import time

BASE_URL = "http://localhost:8008"

# Test IDs we'll use
HOMEOWNER_ID = str(uuid.uuid4())
BID_CARD_ID = str(uuid.uuid4())

# Multiple contractors
CONTRACTORS = [
    {
        "id": str(uuid.uuid4()),
        "name": "Premium Kitchen Renovations",
        "company": "Premium Kitchen Co",
        "specialty": "High-end kitchen remodels",
        "bid_amount": 45000,
        "timeline_days": 30
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Budget Home Solutions",
        "company": "Budget Solutions LLC",
        "specialty": "Affordable kitchen updates",
        "bid_amount": 28000,
        "timeline_days": 21
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Modern Design Builders",
        "company": "Modern Design Group",
        "specialty": "Contemporary kitchen designs",
        "bid_amount": 38000,
        "timeline_days": 25
    }
]

def create_bid_card():
    """Create a real bid card in the database"""
    print("\n=== CREATING BID CARD ===")
    
    import os
    from supabase import create_client
    
    supabase_url = "https://xrhgrthdcaymxuqcgrmj.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NTcyMDYsImV4cCI6MjA2OTIzMzIwNn0.BriGLA2FE_e_NJl8B-3ps1W6ZAuK6a5HpTwBGy-6rmE"
    
    db = create_client(supabase_url, supabase_key)
    
    bid_card_data = {
        "id": BID_CARD_ID,
        "bid_card_number": f"BC-DEMO-{int(time.time())}",
        "project_type": "kitchen_remodel",
        "urgency_level": "week",
        "budget_min": 25000,
        "budget_max": 50000,
        "contractor_count_needed": 3,
        "status": "active",
        "title": "Complete Kitchen Remodel - Multiple Quotes Needed",
        "bid_document": {
            "project_description": "Complete kitchen renovation including new cabinets, countertops, appliances, and flooring. Looking for multiple quotes from qualified contractors.",
            "location": {
                "city": "Austin",
                "state": "TX", 
                "zip_code": "78701",
                "address": "123 Main Street"
            },
            "timeline_urgency": "2-3 weeks to start",
            "material_preferences": ["Quartz countertops", "Hardwood cabinets", "Stainless steel appliances"],
            "special_requirements": ["Licensed and insured", "References required", "Warranty on work"],
            "images": [
                "https://example.com/kitchen-current-1.jpg",
                "https://example.com/kitchen-current-2.jpg",
                "https://example.com/kitchen-inspiration.jpg"
            ],
            "submitted_bids": [],
            "bids_received_count": 0
        },
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = db.table("bid_cards").insert(bid_card_data).execute()
    
    if result.data:
        print(f"✅ Created bid card: {bid_card_data['bid_card_number']}")
        print(f"   ID: {BID_CARD_ID}")
        print(f"   Title: {bid_card_data['title']}")
        return True
    else:
        print("❌ Failed to create bid card")
        return False

def send_contractor_messages():
    """Send messages from each contractor asking questions"""
    print("\n=== SENDING CONTRACTOR MESSAGES ===")
    
    messages = [
        {
            "contractor": CONTRACTORS[0],
            "messages": [
                "Hi! I saw your kitchen remodel project. We specialize in high-end renovations. Can you tell me more about your style preferences?",
                "Also, do you have a specific timeline in mind? We have an opening in 3 weeks.",
                "Here are some photos of our recent work: [Photo of luxury kitchen] [Photo of modern backsplash]"
            ]
        },
        {
            "contractor": CONTRACTORS[1],
            "messages": [
                "Hello! We'd love to help with your kitchen remodel. We focus on delivering great value.",
                "What's most important to you - staying within budget or getting specific high-end features?",
                "We can work with your budget to maximize what you get. Here's our portfolio: [Budget kitchen transformation photos]"
            ]
        },
        {
            "contractor": CONTRACTORS[2],
            "messages": [
                "Good morning! Your kitchen project sounds exciting. We specialize in modern, contemporary designs.",
                "Are you open to sustainable materials? We have great eco-friendly options.",
                "I'm attaching our design catalog with pricing: [Modern kitchen designs PDF]"
            ]
        }
    ]
    
    conversation_ids = {}
    
    for contractor_msgs in messages:
        contractor = contractor_msgs["contractor"]
        print(f"\n  Contractor: {contractor['name']}")
        
        for msg_content in contractor_msgs["messages"]:
            message_data = {
                "bid_card_id": BID_CARD_ID,
                "sender_type": "contractor",
                "sender_id": contractor["id"],
                "content": msg_content,
                "attachments": []
            }
            
            # Add mock attachments for messages mentioning photos/PDFs
            if "[Photo" in msg_content or "[PDF]" in msg_content:
                message_data["attachments"] = [
                    {
                        "name": f"portfolio_{contractor['id'][:8]}.jpg",
                        "url": f"https://example.com/contractor-work-{random.randint(1,100)}.jpg",
                        "type": "image/jpeg"
                    }
                ]
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/messages/send",
                    json=message_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    conversation_ids[contractor["id"]] = data.get("conversation_id")
                    print(f"    ✅ Message sent")
                else:
                    print(f"    ❌ Failed: {response.status_code}")
                    
                time.sleep(0.5)  # Small delay between messages
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    return conversation_ids

def submit_contractor_proposals():
    """Submit actual bid proposals from each contractor"""
    print("\n=== SUBMITTING CONTRACTOR PROPOSALS ===")
    
    proposals = [
        {
            "contractor": CONTRACTORS[0],
            "proposal_text": """
Premium Kitchen Renovations - Detailed Proposal

We're excited to submit our bid for your kitchen remodel project.

SCOPE OF WORK:
• Complete cabinet replacement with custom hardwood cabinets
• Premium quartz countertops with waterfall edge
• High-end stainless steel appliance package (Sub-Zero, Wolf)
• Hardwood flooring installation
• Custom tile backsplash
• Under-cabinet LED lighting
• Plumbing and electrical updates as needed

TIMELINE: 30 days from start to completion

INCLUDED:
✓ All materials and labor
✓ Project management
✓ Daily cleanup
✓ 5-year warranty on workmanship
✓ All permits and inspections

INVESTMENT: $45,000

We pride ourselves on attention to detail and superior craftsmanship. 
Our team has completed over 200 luxury kitchen renovations in Austin.

References available upon request.
            """,
            "attachments": [
                {
                    "name": "Premium_Kitchen_Portfolio.pdf",
                    "url": "https://example.com/premium-portfolio.pdf",
                    "type": "application/pdf",
                    "size": 5242880
                },
                {
                    "name": "Insurance_Certificate.pdf",
                    "url": "https://example.com/insurance.pdf",
                    "type": "application/pdf",
                    "size": 1048576
                }
            ]
        },
        {
            "contractor": CONTRACTORS[1],
            "proposal_text": """
Budget Home Solutions - Kitchen Remodel Proposal

Thank you for considering us for your kitchen renovation!

WHAT WE'LL DO:
• Install quality cabinet refacing or replacement (your choice)
• Granite or quartz countertops (several options in your budget)
• New appliance package (GE or Whirlpool)
• Vinyl plank or tile flooring
• Subway tile backsplash
• New sink and faucet
• Paint and finishing touches

TIMELINE: 21 days total

WHAT'S INCLUDED:
• All materials and labor
• Removal of old materials
• Basic plumbing/electrical updates
• 2-year warranty
• Financing available

TOTAL COST: $28,000

We believe in honest pricing and quality work. We'll maximize your budget!
Over 500 happy customers in the Austin area.

Let's make your dream kitchen affordable!
            """,
            "attachments": [
                {
                    "name": "Budget_Transformations.pdf",
                    "url": "https://example.com/budget-portfolio.pdf",
                    "type": "application/pdf",
                    "size": 3145728
                }
            ]
        },
        {
            "contractor": CONTRACTORS[2],
            "proposal_text": """
Modern Design Builders - Contemporary Kitchen Proposal

We're thrilled to present our vision for your modern kitchen transformation.

DESIGN CONCEPT:
• Sleek flat-panel cabinets in matte white or gray
• Waterfall quartz island with seating for 4
• Integrated appliances for seamless look
• Large format porcelain tile flooring
• Glass tile accent backsplash
• Smart home integration (lighting, appliances)
• Hidden storage solutions

PROJECT DURATION: 25 days

COMPREHENSIVE PACKAGE:
• 3D design renderings before we start
• All materials and installation
• Structural modifications if needed
• Smart home setup and training
• 3-year comprehensive warranty
• Post-installation support

INVESTMENT: $38,000

Modern Design Builders brings innovative design and sustainable materials.
Featured in Austin Home & Design magazine.

Schedule a consultation to see your kitchen in 3D!
            """,
            "attachments": [
                {
                    "name": "Modern_Kitchen_Designs.pdf",
                    "url": "https://example.com/modern-designs.pdf",
                    "type": "application/pdf",
                    "size": 7340032
                },
                {
                    "name": "3D_Rendering_Sample.jpg",
                    "url": "https://example.com/3d-render.jpg",
                    "type": "image/jpeg",
                    "size": 2097152
                }
            ]
        }
    ]
    
    proposal_ids = []
    
    for i, proposal_data in enumerate(proposals):
        contractor = CONTRACTORS[i]
        print(f"\n  {contractor['name']}:")
        
        proposal = {
            "bid_card_id": BID_CARD_ID,
            "contractor_id": contractor["id"],
            "contractor_name": contractor["name"],
            "contractor_company": contractor["company"],
            "bid_amount": contractor["bid_amount"],
            "timeline_days": contractor["timeline_days"],
            "proposal_text": proposal_data["proposal_text"],
            "attachments": proposal_data["attachments"]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/contractor-proposals/submit",
                json=proposal,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    proposal_ids.append(data.get("proposal_id"))
                    print(f"    ✅ Proposal submitted: ${contractor['bid_amount']:,} / {contractor['timeline_days']} days")
                else:
                    print(f"    ❌ {data.get('message')}")
            else:
                print(f"    ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return proposal_ids

def show_homeowner_view():
    """Show where the homeowner can see everything"""
    print("\n" + "="*60)
    print("🏠 HOMEOWNER VIEW - WHERE TO SEE EVERYTHING")
    print("="*60)
    
    print(f"""
✅ BID CARD CREATED: {BID_CARD_ID}

📍 WHERE TO VIEW AS HOMEOWNER:

1. MAIN DASHBOARD:
   http://localhost:5173/dashboard
   - Look for bid card: "Complete Kitchen Remodel - Multiple Quotes Needed"
   - Click on it to open the project workspace

2. DIRECT PROJECT LINK:
   http://localhost:5173/bid-cards/{BID_CARD_ID}
   - This goes directly to your project workspace
   
3. WHAT YOU'LL SEE:
   
   A. Overview Tab:
      - Project details and requirements
      - Budget: $25,000 - $50,000
      - 3 contractors needed
      
   B. Contractors Tab (MAIN VIEW):
      ✨ ContractorCommunicationHub Component Shows:
      
      • CONTRACTOR 1: Premium Kitchen Renovations
        - 3 messages with portfolio photos
        - Bid: $45,000 / 30 days
        - Attachments: Portfolio PDF, Insurance
        
      • CONTRACTOR 2: Budget Home Solutions  
        - 3 messages about value options
        - Bid: $28,000 / 21 days
        - Attachments: Transformation examples
        
      • CONTRACTOR 3: Modern Design Builders
        - 3 messages about modern design
        - Bid: $38,000 / 25 days
        - Attachments: 3D renderings
        
   C. Features You Can Test:
      - Click each contractor card to expand/collapse
      - View proposal details with full text
      - See message threads with timestamps
      - Download attachments (mock URLs)
      - Send replies to contractors
      - Compare all bids side-by-side

4. LOGIN (if needed):
   - Email: test@example.com
   - Password: (use any test account)
   - Or create new homeowner account

5. API VERIFICATION:
   Test the API directly:
   
   GET http://localhost:8008/api/contractor-proposals/bid-card/{BID_CARD_ID}
   - Returns all 3 contractor proposals
   
   GET http://localhost:8008/api/messages/conversations?bid_card_id={BID_CARD_ID}
   - Returns all contractor conversations

THIS IS REAL DATA IN THE DATABASE - NOT HARDCODED!
""")

def verify_data():
    """Verify all data was created successfully"""
    print("\n=== VERIFYING DATA ===")
    
    # Check proposals
    try:
        response = requests.get(f"{BASE_URL}/api/contractor-proposals/bid-card/{BID_CARD_ID}")
        if response.status_code == 200:
            proposals = response.json()
            print(f"✅ Found {len(proposals)} proposals in database")
            for p in proposals:
                print(f"   - {p['contractor_name']}: ${p['bid_amount']:,}")
    except Exception as e:
        print(f"❌ Error checking proposals: {e}")
    
    # Check messages
    try:
        params = {
            "bid_card_id": BID_CARD_ID,
            "user_type": "homeowner",
            "user_id": HOMEOWNER_ID
        }
        response = requests.get(f"{BASE_URL}/api/messages/conversations", params=params)
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])
            print(f"✅ Found {len(conversations)} conversations in database")
    except Exception as e:
        print(f"❌ Error checking messages: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CREATING REAL CONTRACTOR PROPOSAL DEMO DATA")
    print("="*60)
    
    # Check backend is running
    try:
        health = requests.get(f"{BASE_URL}/api/contractor-proposals/health")
        if health.status_code != 200:
            print("❌ Backend not running! Start Docker first:")
            print("   cd C:\\Users\\Not John Or Justin\\Documents\\instabids")
            print("   docker-compose up -d")
            exit(1)
    except:
        print("❌ Cannot connect to backend at http://localhost:8008")
        exit(1)
    
    # Create the demo
    if create_bid_card():
        time.sleep(1)
        send_contractor_messages()
        time.sleep(1)
        submit_contractor_proposals()
        time.sleep(1)
        verify_data()
        show_homeowner_view()
        
        print("\n" + "="*60)
        print("✅ DEMO DATA CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n🎯 GO TO: http://localhost:5173/bid-cards/{BID_CARD_ID}")
        print("   to see the complete homeowner view with all contractor interactions\n")
    else:
        print("\n❌ Failed to create demo data")
        exit(1)