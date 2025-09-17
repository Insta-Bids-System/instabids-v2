import requests
import os
from datetime import datetime

# The generated image URL
image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-XbuLu3W08vzqjwSOLNAQHWLb/user-ulYaQfAoRoaE5j0IF3KcRnA1/img-mkYMvfadNuBYDYbjXigdiXqi.png?st=2025-07-30T03%3A23%3A16Z&se=2025-07-30T05%3A23%3A16Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=cc612491-d948-4d2e-9821-2683df3719f5&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-07-29T23%3A30%3A07Z&ske=2025-07-30T23%3A30%3A07Z&sks=b&skv=2024-08-04&sig=gSOE4P/82/cKrOHaT7u48xNWWdjgb9zKn0yVZWtnFdA%3D"

print("Downloading the generated backyard image...")

try:
    # Download the image
    response = requests.get(image_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code == 200:
        # Save it locally
        filename = f"generated_backyard_turf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join("test-images", filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"[SUCCESS] Image saved to: {filepath}")
        print(f"Full path: {os.path.abspath(filepath)}")
        
        # Also save to the main directory for easy access
        main_filepath = "YOUR_GENERATED_BACKYARD.png"
        with open(main_filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"\n[SAVED] Also saved as: {os.path.abspath(main_filepath)}")
        
        # Create a simple HTML viewer
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Your Generated Backyard</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            text-align: center;
        }}
        h1 {{ color: #2e7d32; }}
        img {{ 
            width: 100%; 
            max-width: 1024px; 
            border: 3px solid #4CAF50;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }}
        .success {{ 
            background: #4CAF50; 
            color: white; 
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>Your AI-Generated Backyard with Artificial Turf</h1>
    <div class="success">
        <h2>Successfully Generated!</h2>
        <p>DALL-E 3 has transformed your patchy backyard into one with beautiful artificial turf!</p>
    </div>
    <img src="{main_filepath}" alt="Your generated backyard with turf">
    <p>The AI kept your soccer goal and all landscaping while replacing the patchy grass with perfect turf.</p>
</body>
</html>"""
        
        with open("VIEW_YOUR_BACKYARD.html", 'w') as f:
            f.write(html_content)
            
        print(f"\n[BROWSER] View in browser: {os.path.abspath('VIEW_YOUR_BACKYARD.html')}")
        
    else:
        print(f"[ERROR] Failed to download: {response.status_code}")
        print("The URL may have expired. Let me generate a new one...")
        
except Exception as e:
    print(f"Error downloading: {e}")