from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a gradient background
width, height = 400, 300
image = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(image)

# Create gradient
for y in range(height):
    r = int((74 + (123 - 74) * y / height))
    g = int((144 + (104 - 144) * y / height))
    b = int((226 + (238 - 226) * y / height))
    draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))

# Add text
try:
    font = ImageFont.truetype("arial.ttf", 30)
    small_font = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# Draw text with outline for better visibility
text1 = "Test Image"
text2 = "For Contractor Upload"

# Get text bounding box
bbox1 = draw.textbbox((width//2, height//2 - 20), text1, font=font, anchor="mm")
bbox2 = draw.textbbox((width//2, height//2 + 20), text2, font=small_font, anchor="mm")

# Draw text
draw.text((width//2, height//2 - 20), text1, fill='white', font=font, anchor="mm")
draw.text((width//2, height//2 + 20), text2, fill='white', font=small_font, anchor="mm")

# Save the image
output_path = r"C:\Users\Not John Or Justin\Downloads\test_contractor_image.png"
image.save(output_path, 'PNG')
print(f"Image saved to: {output_path}")