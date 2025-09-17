from PIL import Image, ImageDraw

# Create a simple test image
img = Image.new('RGB', (800, 600), color='lightblue')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 750, 550], outline='black', width=3)
draw.text((300, 280), "Test Kitchen Image", fill='black')
img.save('C:\\Users\\Not John Or Justin\\Documents\\instabids\\test_kitchen.jpg')
print("Test image created!")