import requests
import base64
import json
from PIL import Image, ImageDraw
import io

# Create a test image with obvious maintenance issues
img = Image.new('RGB', (800, 600), color='beige')
draw = ImageDraw.Draw(img)

# Draw some basic room elements
draw.rectangle([50, 100, 300, 400], outline='brown', width=3)  # Window with broken blinds
draw.line([50, 150, 300, 150], fill='gray', width=2)  # Broken blind slat
draw.line([50, 200, 280, 220], fill='gray', width=2)  # Tilted blind slat
draw.text((100, 120), "BROKEN BLINDS", fill='red')

# Water damage on wall
draw.ellipse([400, 200, 550, 350], outline='brown', fill='tan')
draw.text((420, 250), "WATER STAIN", fill='brown')

# Cracked wall
draw.line([600, 100, 650, 300], fill='black', width=3)
draw.text((590, 320), "CRACK", fill='black')

# Save to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Test the property API with GPT-5
print("Testing property API with GPT-5 image analysis...")
print("-" * 50)

# First need a property ID - use a test property
property_id = "test-property-123"

# Create multipart form data
files = {
    'file': ('living_room_damage.png', img_bytes.getvalue(), 'image/png')
}
data = {
    'photo_type': 'documentation',
    'user_id': 'test-user-123'
}

response = requests.post(
    f'http://localhost:8008/{property_id}/photos/upload',
    files=files,
    data=data
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Check if GPT-5 was actually used
if response.status_code == 200:
    result = response.json()
    if 'classification' in result:
        print("\n✅ ANALYSIS RESULTS:")
        print(f"Room Type: {result['classification'].get('room_type', 'Unknown')}")
        print(f"Confidence: {result['classification'].get('confidence', 0)*100:.1f}%")
        
        if 'issues_detected' in result['classification']:
            print(f"\n🔴 MAINTENANCE ISSUES DETECTED:")
            for issue in result['classification']['issues_detected']:
                print(f"  - {issue}")
        
        if 'assets_detected' in result['classification']:
            print(f"\n📦 ASSETS DETECTED: {len(result['classification']['assets_detected'])}")
            for asset in result['classification']['assets_detected'][:3]:
                print(f"  - {asset}")
        
        # Most important - check if this is REAL AI or fallback
        if result['classification'].get('confidence', 0) == 0.75:
            print("\n⚠️ WARNING: This might be using FALLBACK classification (confidence exactly 0.75)")
        else:
            print("\n✅ Using REAL GPT-5 AI analysis (not fallback)")
else:
    print(f"\n❌ Error: {response.text}")