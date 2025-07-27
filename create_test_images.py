from PIL import Image, ImageDraw, ImageFont
import os
import random

# Create images directory if it doesn't exist
os.makedirs("images", exist_ok=True)

colors = [
    (255, 100, 100),  # Red
    (100, 255, 100),  # Green  
    (100, 100, 255),  # Blue
    (255, 255, 100),  # Yellow
    (255, 100, 255),  # Magenta
    (100, 255, 255),  # Cyan
    (255, 150, 100),  # Orange
    (150, 100, 255),  # Purple
    (100, 200, 150),  # Teal
    (200, 150, 255),  # Lavender
]

# Generate 15 images: 70% portrait (11 images), 30% landscape (4 images)
total_images = 15
portrait_count = 11
landscape_count = 4

image_count = 0

# Generate portrait images first
for i in range(portrait_count):
    # Portrait: 9:16 aspect ratio
    width = 900
    height = 1600
    
    # Create new image with gradient background
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Create gradient
    color1 = colors[i % len(colors)]
    color2 = tuple(max(0, c - 100) for c in color1)
    
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Add text
    text = f"Portrait {i + 1}"
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with shadow
    draw.text((x + 5, y + 5), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    # Save image
    image_count += 1
    img.save(f"images/test_image_{image_count:02d}.jpg", quality=90)
    print(f"Created test_image_{image_count:02d}.jpg (Portrait)")

# Generate landscape images
for i in range(landscape_count):
    # Landscape: 16:9 aspect ratio
    width = 1600
    height = 900
    
    # Create new image with gradient background
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Create gradient
    color_index = (portrait_count + i) % len(colors)
    color1 = colors[color_index]
    color2 = tuple(max(0, c - 100) for c in color1)
    
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Add text
    text = f"Landscape {i + 1}"
    try:
        # Try to use a better font if available
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with shadow
    draw.text((x + 5, y + 5), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    
    # Save image
    image_count += 1
    img.save(f"images/test_image_{image_count:02d}.jpg", quality=90)
    print(f"Created test_image_{image_count:02d}.jpg (Landscape)")

print(f"\nTest images created successfully!")
print(f"Total: {total_images} images ({portrait_count} portrait, {landscape_count} landscape)")
print("You can now run: uv run python main.py")