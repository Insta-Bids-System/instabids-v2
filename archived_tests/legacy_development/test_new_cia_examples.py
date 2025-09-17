"""
Example Conversations Using New Pain-Point First CIA Approach
Demonstrates how the redesigned prompts work in practice
"""
import sys
import io
# Set output encoding to UTF-8 to handle emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Example 1: Opening Chat Experience with Pre-loaded Message
print("=" * 60)
print("EXAMPLE 1: CHAT OPENS WITH PRE-LOADED MESSAGE")
print("=" * 60)
print()
print("[Chat UI opens - message already displayed]")
print()
print("InstaBids AI:")
print("""
Welcome to InstaBids! 🏠

We're solving the REAL problems of home improvement:

💰 **Save 10-25% on Every Project**
Contractors on InstaBids offer lower prices because they don't pay $500-$3,000 lead fees. You keep that money.

📷 **Photos = Accurate Quotes (No Sales Meetings!)**
Upload photos, get real quotes. No more wasting Saturday mornings with sales reps.

👥 **Group Bidding = 15-25% MORE Savings**
Got neighbors who need work too? Bundle projects for massive additional discounts!

🎯 **Choose Your Contractor Type**
From your neighbor with a truck to national companies - you pick who bids.

🚫 **Zero Sales Pressure**
All communication through our platform. Your phone number stays private.

🤖 **AI That Remembers Everything**
I'll remember your home, preferences, and every project forever.

💡 **Instant Project Ideas from Photos**
Show me any room and I'll suggest improvements with estimated costs.

**Ready to save thousands?** Just tell me about your project or upload a photo!
""")
print()
print("User: My deck is falling apart and needs to be rebuilt")
print()
print("InstaBids AI:")
print("""
I can definitely help you get that deck rebuilt while saving you serious money! Let me gather some details to get you accurate quotes from contractors.

**Quick question first** - Are you looking to rebuild with the same materials (like-for-like replacement) or are you considering upgrades like composite decking or different design?

And to get you the best pricing - do any of your neighbors have deck work they need? Group bidding typically saves an additional 15-25% on top of our already lower prices!

While we chat, feel free to upload photos of your current deck - contractors give much more accurate quotes when they can see exactly what they're working with.
""")
print()

# Example 2: Photo-First Interaction
print("=" * 60)
print("EXAMPLE 2: PHOTO-FIRST STRATEGY")
print("=" * 60)
print()
print("User: [Uploads photo of damaged roof]")
print()
print("InstaBids AI:")
print("""
Great photo - I can see exactly what we're dealing with! I notice:
- Missing shingles on the northeast section
- Some visible water damage near the chimney flashing
- Gutters appear to be sagging on the left side

**This looks URGENT** - with potential water damage, you'll want this addressed quickly to prevent interior problems.

Since this is urgent, I'll prioritize getting you quotes from contractors who can start ASAP. Our Tier 2 contractors (owner-operated teams) are usually fastest for urgent roof repairs while still being insured and professional.

**Critical question**: Are you seeing any water spots on your ceilings inside? This helps determine if we need emergency tarping while scheduling the full repair.

**Money-saving opportunity**: I noticed your neighbor's roof (visible in the photo) has similar aging. If they need work too, you could both save 15-25% by having the same crew do both roofs!
""")
print()

# Example 3: Quality Level Internal Assessment (Never Mentioned)
print("=" * 60)
print("EXAMPLE 3: INTERNAL QUALITY ASSESSMENT")
print("=" * 60)
print()
print("User: We want to redo our kitchen with high-end finishes, Viking appliances, and custom cabinetry")
print()
print("InstaBids AI:")
print("""
Excellent! A full kitchen transformation with professional-grade appliances and custom work - this is going to be stunning!

For a project of this caliber, you'll want contractors who specialize in luxury renovations and have relationships with high-end suppliers. They often get designer discounts on Viking and similar brands that they can pass along.

**Photos are CRUCIAL here** - custom cabinetry pricing varies wildly based on your exact layout. Can you upload photos of your current kitchen from multiple angles? Contractors will also want to see:
- Where your plumbing and electrical enter the space
- Window and door locations
- Any walls you're considering removing

**Project phasing question**: Would you prefer to do this all at once (typically 6-8 weeks) or phase it to maintain some kitchen access? Phasing costs more but keeps you functional.

[INTERNAL: Setting quality_level = PREMIUM, contractor_tier = 3-4, ensure insurance verification]
""")
print()

# Example 4: Group Bidding Opportunity Detection
print("=" * 60)
print("EXAMPLE 4: GROUP BIDDING EMPHASIS")
print("=" * 60)
print()
print("User: I need my driveway sealed before winter")
print()
print("InstaBids AI:")
print("""
Perfect timing for driveway sealing! Fall is ideal - the cooler temperatures help the sealant cure properly.

**MASSIVE SAVINGS OPPORTUNITY!** 🎯
Driveway sealing is PERFECT for group bidding! Contractors bring all their equipment and materials to your neighborhood once, dramatically reducing their costs. Here's what we typically see:

- Solo driveway: $300-400
- 3 driveways together: $225-275 each (25% savings!)
- 5+ driveways: $200-240 each (35% savings!)

**Do you know if any neighbors need sealing?** I can create a group bid card that they can join. Even just one neighbor joining saves you both serious money.

Quick details I need:
- Approximate driveway size (or car capacity - 2 car, 3 car, etc.)
- Any cracks that need filling first?
- Last time it was sealed?

Want me to create a shareable link for your neighbors? You could post it on Nextdoor or your HOA Facebook group!
""")
print()

# Example 5: No More Sales Meetings Emphasis
print("=" * 60)
print("EXAMPLE 5: ELIMINATING SALES MEETINGS")
print("=" * 60)
print()
print("User: I need new windows but I HATE having salespeople in my house")
print()
print("InstaBids AI:")
print("""
You're going to LOVE this - InstaBids completely eliminates those painful 3-hour sales presentations! 🙌

Here's how we're different:
- **No phone number shared** - Everything happens through our platform
- **No in-person sales pitches** - Contractors submit quotes based on photos
- **No pressure tactics** - Review bids on YOUR schedule
- **No "today only" deals** - All prices are real, sustainable prices

For windows, contractors can give you accurate quotes from photos showing:
- Each window from inside and outside
- Close-ups of any damage or problem areas
- Full room shots for context
- Your home's exterior (for style matching)

The quotes you'll receive will include:
- Exact window specifications and energy ratings
- Total cost with installation
- Timeline for completion
- Warranty details

**Would you prefer to start with just problem windows or get quotes for whole-house replacement?** Many homeowners do problem windows first, then use the savings for the rest!

I'll keep all your info private - contractors only get your project details, never your contact information until YOU choose to hire someone.
""")
print()

print("=" * 60)
print("KEY IMPROVEMENTS IN NEW APPROACH:")
print("=" * 60)
print("""
1. ✅ PAIN POINTS FIRST - Opens with solving real problems
2. ✅ PHOTO EMPHASIS - Every response encourages photos
3. ✅ QUALITY INTERNAL - Never asks "basic or premium?"
4. ✅ GROUP BIDDING CENTRAL - Mentioned in every relevant scenario
5. ✅ PRIVACY PROTECTION - Emphasizes no phone sharing
6. ✅ NO SALES MEETINGS - Major selling point highlighted
7. ✅ PERSISTENT MEMORY - "I'll remember everything"
8. ✅ PRE-LOADED OPENING - Chat starts with value proposition
""")