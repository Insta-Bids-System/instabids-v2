from PIL import Image, ImageDraw, ImageFont
import io

# Create an ideal kitchen inspiration image
img = Image.new('RGB', (600, 400), color='white')
draw = ImageDraw.Draw(img)

# Draw cabinet outlines (white shaker style)
draw.rectangle([50, 150, 550, 300], fill='#f8f8f8', outline='#d4d4d4', width=2)
draw.rectangle([60, 160, 180, 290], fill='white', outline='#333', width=1)
draw.rectangle([190, 160, 310, 290], fill='white', outline='#333', width=1)
draw.rectangle([320, 160, 440, 290], fill='white', outline='#333', width=1)
draw.rectangle([450, 160, 540, 290], fill='white', outline='#333', width=1)

# Draw countertop (marble look)
draw.rectangle([50, 300, 550, 320], fill='#e8e8e8', outline='#ccc', width=1)

# Draw backsplash (subway tiles)
for x in range(60, 540, 40):
    for y in range(120, 150, 15):
        draw.rectangle([x, y, x+35, y+12], fill='white', outline='#ddd', width=1)

# Draw modern hardware (black)
for x in [120, 240, 360, 480]:
    draw.rectangle([x, 220, x+8, 228], fill='black')

# Add pendant lights
draw.ellipse([200, 80, 220, 100], fill='#f4f4f4', outline='black', width=1)
draw.ellipse([380, 80, 400, 100], fill='#f4f4f4', outline='black', width=1)

# Add text overlay
draw.text((300, 30), "Dream Kitchen", fill='#333', anchor='mm')
draw.text((300, 50), "White Shaker • Marble • Black Hardware", fill='#666', anchor='mm')

# Save the image
img.save('C:/Users/Not John Or Justin/Documents/instabids/ideal-kitchen-inspiration.jpg', 'JPEG', quality=90)
print("Created ideal kitchen inspiration image")