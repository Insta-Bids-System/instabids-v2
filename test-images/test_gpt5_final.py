import requests
import base64
import json
from PIL import Image, ImageDraw
import io

print("Creating test image with maintenance issues...")
# Create a test image with obvious maintenance issues
img = Image.new('RGB', (800, 600), color='beige')
draw = ImageDraw.Draw(img)

# Draw room elements with issues
draw.rectangle([50, 100, 300, 400], outline='brown', width=3)  # Window
draw.line([50, 150, 300, 150], fill='gray', width=2)  # Broken blind
draw.text((100, 120), "BROKEN BLINDS", fill='red')
draw.ellipse([400, 200, 550, 350], outline='brown', fill='tan')  # Water stain
draw.text((420, 250), "WATER DAMAGE", fill='brown')

# Save to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

print("\nTesting property API with GPT-5 image analysis...")
print("-" * 50)

# Create multipart form data
files = {
    'file': ('living_room_damage.png', img_bytes.getvalue(), 'image/png')
}
data = {
    'photo_type': 'documentation',
    'user_id': 'test-user-123'
}

# Test the corrected endpoint with query parameter
property_id = "test-property-123"
response = requests.post(
    f'http://localhost:8008/api/properties/{property_id}/photos/upload?user_id=test-user-123',
    files=files,
    data=data
)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if 'classification' in result:
        print("\n=== GPT-5 ANALYSIS RESULTS ===")
        classification = result['classification']
        
        if 'room_type' in classification:
            print(f"Room Type: {classification['room_type']}")
        
        if 'confidence' in classification:
            confidence = classification['confidence']
            print(f"Confidence: {confidence*100:.1f}%")
            
            # Check if this is REAL GPT-5 or fallback
            if confidence == 0.75:
                print("\nWARNING: Using FALLBACK classification (not real AI)")
            else:
                print("\nSUCCESS: Using REAL GPT-5 AI analysis!")
        
        if 'issues_detected' in classification:
            print(f"\nMAINTENANCE ISSUES DETECTED:")
            for issue in classification['issues_detected']:
                print(f"  - {issue}")
        
        if 'assets_detected' in classification:
            print(f"\nASSETS DETECTED: {len(classification['assets_detected'])}")
            for asset in classification['assets_detected'][:5]:
                print(f"  - {asset}")
else:
    print(f"Error: {response.text}")