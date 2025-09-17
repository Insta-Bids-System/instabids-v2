#!/usr/bin/env python3
"""
Create test files with obfuscated contact information
Tests GPT-4o's ability to detect hidden/disguised contact attempts
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont
import os

def create_obfuscated_pdf():
    """Create PDFs with various obfuscation techniques"""
    
    # Test 1: Heavily obfuscated contact info
    pdf_path1 = "obfuscated_heavy.pdf"
    c = canvas.Canvas(pdf_path1, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    content = [
        "KITCHEN RENOVATION PROPOSAL",
        "",
        "Project Details:",
        "- Complete kitchen remodel",
        "- Timeline: 4-6 weeks",
        "",
        "For questions, reach out at:",
        "five five five - one two three - four five six seven",
        "Call me: 5 5 5 . 1 2 3 . 4 5 6 7",
        "Text: (5five5) 123-WORK",
        "",
        "Electronic mail:",
        "john [at] contractor [dot] com",
        "j0hn @ c0ntract0r . c0m",
        "Contact: john(at)contractor(dot)com",
        "",
        "Visit us: One Two Three Main Street",
        "Location: 1 2 3 Main St, Suite 4 5 6",
        "",
        "Social: @contractorjohn on all platforms",
        "Find us: facebook slash contractor john",
        "Instagram: contractor_john_123"
    ]
    
    y = 750
    for line in content:
        c.drawString(100, y, line)
        y -= 20
    
    c.save()
    print(f"Created: {pdf_path1}")
    
    # Test 2: Subtle obfuscation
    pdf_path2 = "obfuscated_subtle.pdf"
    c = canvas.Canvas(pdf_path2, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    content = [
        "PROFESSIONAL BID PROPOSAL",
        "",
        "Scope of Work:",
        "- Bathroom renovation",
        "- New fixtures and tiling",
        "",
        "Questions? Dial 555-O123-4567",  # O instead of 0
        "Mobile: 555.0l23.4567",  # l instead of 1
        "",
        "Email: john@c0mpany.c0m",  # 0 instead of o
        "Alt: j.smith AT contractor DOT net",
        "",
        "Office: l23 Main Street, Unit 2O",  # l for 1, O for 0
        "",
        "WhatsApp: +1 555 123 4567",
        "Telegram: @john_contractor"
    ]
    
    y = 750
    for line in content:
        c.drawString(100, y, line)
        y -= 20
    
    c.save()
    print(f"Created: {pdf_path2}")
    
    # Test 3: Clean PDF (control)
    pdf_path3 = "obfuscated_clean.pdf"
    c = canvas.Canvas(pdf_path3, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    content = [
        "PROFESSIONAL BID PROPOSAL",
        "",
        "Project Overview:",
        "- Complete home renovation",
        "- Premium materials included",
        "- Licensed and insured",
        "",
        "Timeline: Six to eight weeks",
        "Budget: Twenty-five thousand to thirty thousand",
        "",
        "Our company values:",
        "- Quality workmanship",
        "- Timely completion",
        "- Customer satisfaction",
        "",
        "All communication through the platform",
        "Messages will be responded to promptly",
        "Thank you for considering our bid"
    ]
    
    y = 750
    for line in content:
        c.drawString(100, y, line)
        y -= 20
    
    c.save()
    print(f"Created: {pdf_path3}")
    
    return [pdf_path1, pdf_path2, pdf_path3]

def create_obfuscated_images():
    """Create images with text containing obfuscated contact info"""
    
    # Test 1: Image with obvious text overlay
    img1 = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img1)
    
    # Try to use a basic font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    text_lines = [
        "Kitchen Design Proposal",
        "",
        "Call: 555-123-4567",
        "Email: john@contractor.com",
        "Visit: 123 Main Street"
    ]
    
    y = 50
    for line in text_lines:
        d.text((50, y), line, fill='black', font=font)
        y += 30
    
    img1.save("obfuscated_image_obvious.png")
    print("Created: obfuscated_image_obvious.png")
    
    # Test 2: Image with subtle/obfuscated text
    img2 = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img2)
    
    text_lines = [
        "Professional Services",
        "",
        "Contact: five five five - one two three - four five six seven",
        "Electronic: john [at] company [dot] com",
        "Location: One Two Three Main St"
    ]
    
    y = 50
    for line in text_lines:
        d.text((50, y), line, fill='gray', font=font)
        y += 30
    
    img2.save("obfuscated_image_subtle.png")
    print("Created: obfuscated_image_subtle.png")
    
    # Test 3: Clean image (no contact info)
    img3 = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img3)
    
    text_lines = [
        "Project Visualization",
        "",
        "Modern Kitchen Design",
        "Premium Materials",
        "Professional Installation"
    ]
    
    y = 50
    for line in text_lines:
        d.text((50, y), line, fill='black', font=font)
        y += 30
    
    img3.save("obfuscated_image_clean.png")
    print("Created: obfuscated_image_clean.png")
    
    return ["obfuscated_image_obvious.png", "obfuscated_image_subtle.png", "obfuscated_image_clean.png"]

def create_text_files():
    """Create various text files with obfuscated content"""
    
    # Test 1: Heavily obfuscated text file
    with open("obfuscated_heavy.txt", "w") as f:
        f.write("""PROJECT PROPOSAL

Contact Information:
Phone: 5-5-5-1-2-3-4-5-6-7
Alt: five five five dot one two three dot four five six seven
Text: (555) 123-WORK

Email: john [at] contractor [dot] com
Alternative: j0hn@c0ntract0r.c0m
Contact: john(at)contractor(dot)com

Address: 1 2 3 Main Street, Suite 4 5 6
Location: One Two Three Main St

Social Media:
FB: facebook.com/contractorjohn
IG: @contractor_john_123
Twitter: @johncontractor

WhatsApp: +1 555 123 4567
Telegram: @john_contractor
""")
    print("Created: obfuscated_heavy.txt")
    
    # Test 2: Clean text file
    with open("obfuscated_clean.txt", "w") as f:
        f.write("""PROJECT PROPOSAL

Scope of Work:
- Complete renovation
- Premium materials
- Licensed professionals

Timeline: Six to eight weeks
Budget: Competitive pricing

Our Commitment:
- Quality workmanship
- Timely completion
- Platform communication only
- Professional service
""")
    print("Created: obfuscated_clean.txt")
    
    return ["obfuscated_heavy.txt", "obfuscated_clean.txt"]

if __name__ == "__main__":
    print("Creating obfuscated test files...")
    
    # Check for required libraries
    try:
        from reportlab.lib.pagesizes import letter
        pdfs = create_obfuscated_pdf()
    except ImportError:
        print("reportlab not installed - skipping PDF creation")
        print("Install with: pip install reportlab")
        pdfs = []
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        images = create_obfuscated_images()
    except ImportError:
        print("PIL not installed - skipping image creation")
        print("Install with: pip install Pillow")
        images = []
    
    texts = create_text_files()
    
    print("\nTest files created:")
    print("PDFs:", pdfs)
    print("Images:", images)
    print("Text files:", texts)
    
    print("\nObfuscation techniques used:")
    print("- Spelled out numbers (five five five)")
    print("- Spaces between digits (5 5 5 - 1 2 3)")
    print("- Letter substitutions (O for 0, l for 1)")
    print("- Alternative formats ([at], [dot], @)")
    print("- Mixed formats (555-O123-4567)")
    print("- Social media handles")
    print("- International formats (+1 555...)")