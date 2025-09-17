import requests
import base64
from pathlib import Path

# Read the test image
image_path = r"C:\Users\Not John Or Justin\Downloads\test_contractor_image.png"
with open(image_path, 'rb') as f:
    image_data = f.read()

# Create the request
url = "http://localhost:8008/api/images/upload/conversation"
files = {
    'file': ('test_contractor_image.png', image_data, 'image/png')
}
data = {
    'conversation_id': '4c9dfb00-ee77-41da-8b8d-2615dbd31d95_44444444-4444-4444-4444-444444444444',
    'sender_id': '11111111-1111-1111-1111-111111111111',  # Use proper UUID
    'sender_type': 'homeowner'
}

print(f"Uploading image to: {url}")
print(f"Data: {data}")

# Send the request
response = requests.post(url, files=files, data=data)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    result = response.json()
    print(f"\nSuccess! Image URL: {result.get('url')}")
    print(f"Message ID: {result.get('message_id')}")
else:
    print(f"\nFailed to upload image")