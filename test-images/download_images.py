import os
import requests
from PIL import Image
import io

# Create directories for organization
current_state_dir = "current-state"
inspiration_dir = "inspiration"

if not os.path.exists(current_state_dir):
    os.makedirs(current_state_dir)
if not os.path.exists(inspiration_dir):
    os.makedirs(inspiration_dir)

# Dictionary of real stock photo URLs
# These are example URLs from free stock photo sites
images_to_download = {
    "current-state": {
        "kitchen-outdated-1.webp": "https://images.pexels.com/photos/1080721/pexels-photo-1080721.jpeg",
        "kitchen-outdated-2.webp": "https://images.pexels.com/photos/1599791/pexels-photo-1599791.jpeg", 
        "bathroom-outdated-1.webp": "https://images.pexels.com/photos/342800/pexels-photo-342800.jpeg",
        "bathroom-outdated-2.webp": "https://images.pexels.com/photos/1457847/pexels-photo-1457847.jpeg",
        "backyard-neglected-1.webp": "https://images.pexels.com/photos/1029599/pexels-photo-1029599.jpeg",
        "backyard-neglected-2.webp": "https://images.pexels.com/photos/2079246/pexels-photo-2079246.jpeg",
        "lawn-problem-1.webp": "https://images.pexels.com/photos/1179229/pexels-photo-1179229.jpeg",
        "lawn-problem-2.webp": "https://images.pexels.com/photos/1072824/pexels-photo-1072824.jpeg"
    },
    "inspiration": {
        "kitchen-modern-1.webp": "https://images.pexels.com/photos/1080696/pexels-photo-1080696.jpeg",
        "kitchen-modern-2.webp": "https://images.pexels.com/photos/2724748/pexels-photo-2724748.jpeg",
        "kitchen-modern-3.webp": "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg",
        "bathroom-luxury-1.webp": "https://images.pexels.com/photos/1454804/pexels-photo-1454804.jpeg",
        "bathroom-luxury-2.webp": "https://images.pexels.com/photos/1358912/pexels-photo-1358912.jpeg",
        "bathroom-luxury-3.webp": "https://images.pexels.com/photos/3315291/pexels-photo-3315291.jpeg",
        "backyard-beautiful-1.webp": "https://images.pexels.com/photos/1029596/pexels-photo-1029596.jpeg",
        "backyard-beautiful-2.webp": "https://images.pexels.com/photos/413195/pexels-photo-413195.jpeg",
        "backyard-beautiful-3.webp": "https://images.pexels.com/photos/534151/pexels-photo-534151.jpeg",
        "lawn-perfect-1.webp": "https://images.pexels.com/photos/1072821/pexels-photo-1072821.jpeg",
        "lawn-perfect-2.webp": "https://images.pexels.com/photos/65280/pexels-photo-65280.jpeg"
    }
}

def download_and_convert_to_webp(url, output_path):
    try:
        # Download image
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Open image and convert to WebP
        img = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if necessary (WebP doesn't support all modes)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as WebP
        img.save(output_path, 'WEBP', quality=85)
        print(f"[OK] Downloaded and converted: {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {output_path}: {str(e)}")
        return False

# Download all images
total = 0
successful = 0

for category, images in images_to_download.items():
    print(f"\nDownloading {category} images...")
    for filename, url in images.items():
        output_path = os.path.join(category, filename)
        total += 1
        if download_and_convert_to_webp(url, output_path):
            successful += 1

print(f"\n[COMPLETE] Download complete: {successful}/{total} images successfully downloaded")
print(f"\nImages are organized in:")
print(f"  - {current_state_dir}/ : Photos of areas needing renovation")
print(f"  - {inspiration_dir}/ : Beautiful, modern inspiration photos")
