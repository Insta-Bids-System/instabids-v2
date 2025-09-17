from PIL import Image, ImageDraw, ImageFont
import os

# Create image
width, height = 800, 600
image = Image.new('RGB', (width, height), '#F5E6D3')  # Beige background
draw = ImageDraw.Draw(image)

# Try to load font, fallback to default
try:
    title_font = ImageFont.truetype("arial.ttf", 24)
    text_font = ImageFont.truetype("arial.ttf", 16)
    small_font = ImageFont.truetype("arial.ttf", 12)
except:
    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# Title
draw.text((250, 50), 'CURRENT KITCHEN - NEEDS UPDATING', fill='#333', font=title_font)

# Old cabinets - brown wood
draw.rectangle([50, 100, 350, 300], fill='#8B4513')  # Left cabinets
draw.rectangle([450, 100, 750, 300], fill='#8B4513')  # Right cabinets

# Cabinet doors
for i in range(4):
    draw.rectangle([60 + i*70, 110, 120 + i*70, 190], outline='#654321', width=3)
    draw.rectangle([460 + i*70, 110, 520 + i*70, 190], outline='#654321', width=3)

# Old countertops - worn laminate
draw.rectangle([50, 300, 750, 360], fill='#D2B48C')

# Old appliances
draw.rectangle([400, 120, 460, 300], fill='#F8F8FF')
draw.text((405, 140), 'OLD FRIDGE', fill='#333', font=small_font)

# Dated sink
draw.rectangle([150, 310, 250, 350], fill='#E6E6FA')
draw.text((165, 325), 'OLD SINK', fill='#333', font=small_font)

# Poor lighting
draw.ellipse([370, 50, 430, 110], fill='#FFE4B5')
draw.text((385, 75), 'OLD LIGHT', fill='#333', font=small_font)

# Problems annotations
problems = [
    '• Dated brown cabinets',
    '• Worn laminate countertops', 
    '• Poor task lighting',
    '• Old appliances need replacing'
]

more_problems = [
    '• Beige walls feel outdated',
    '• Limited storage space',
    '• Needs modern hardware', 
    '• Overall tired appearance'
]

y_pos = 450
for problem in problems:
    draw.text((50, y_pos), problem, fill='#FF4500', font=text_font)
    y_pos += 30

y_pos = 450
for problem in more_problems:
    draw.text((400, y_pos), problem, fill='#FF4500', font=text_font)
    y_pos += 30

# Save image
image_path = "C:\\Users\\Not John Or Justin\\Documents\\instabids\\test-current-kitchen.png"
image.save(image_path)
print(f"Created test current kitchen image: {image_path}")