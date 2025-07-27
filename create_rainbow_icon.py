#!/usr/bin/env python3
"""
Create rainbow-striped app icon for Reel 77
Based on the provided design with horizontal rainbow stripes
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_rainbow_icon(size):
    """Create a single icon at the specified size with rainbow stripes"""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Define rainbow colors (top to bottom)
    colors = [
        '#D85652',  # Red/coral
        '#E89B5C',  # Orange
        '#F9F871',  # Yellow
        '#B8E986',  # Light green
        '#7ED3C4',  # Cyan/turquoise
        '#6B9BD1',  # Light blue
        '#5E5BBF',  # Purple/indigo
    ]
    
    # Draw rounded rectangle background
    corner_radius = size // 12
    
    # Calculate stripe height
    stripe_height = size // len(colors)
    
    # Create a mask for rounded corners
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size-1, size-1)], 
                                radius=corner_radius, fill=255)
    
    # Draw stripes
    for i, color in enumerate(colors):
        y_start = i * stripe_height
        y_end = (i + 1) * stripe_height if i < len(colors) - 1 else size
        draw.rectangle([(0, y_start), (size, y_end)], fill=color)
    
    # Apply rounded corners mask
    rounded_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    rounded_img.paste(img, (0, 0), mask)
    img = rounded_img
    draw = ImageDraw.Draw(img)
    
    # Add "REEL" text
    try:
        # Try to find a bold font
        font_size_reel = int(size * 0.35)
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/Avenir Next.ttc',
            '/Library/Fonts/Arial Bold.ttf',
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
        ]
        font_reel = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_reel = ImageFont.truetype(font_path, font_size_reel, index=1)  # Try bold variant
                    break
                except:
                    try:
                        font_reel = ImageFont.truetype(font_path, font_size_reel)
                        break
                    except:
                        continue
        
        if not font_reel:
            font_reel = ImageFont.load_default()
        
        # Draw "REEL" text in white with shadow
        text = "REEL"
        bbox = draw.textbbox((0, 0), text, font=font_reel)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position in the green stripe area (middle-upper part)
        text_x = (size - text_width) // 2
        text_y = int(size * 0.3)  # Adjust to be in the green area
        
        # Draw shadow
        shadow_offset = max(2, size // 128)
        draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
                 fill=(0, 0, 0, 128), font=font_reel)
        
        # Draw main text
        draw.text((text_x, text_y), text, fill='white', font=font_reel)
        
        # Add "77" text
        font_size_77 = int(size * 0.28)
        font_77 = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_77 = ImageFont.truetype(font_path, font_size_77, index=1)
                    break
                except:
                    try:
                        font_77 = ImageFont.truetype(font_path, font_size_77)
                        break
                    except:
                        continue
        
        if not font_77:
            font_77 = font_reel  # Fallback to same font
        
        text_77 = "77"
        bbox_77 = draw.textbbox((0, 0), text_77, font=font_77)
        text_width_77 = bbox_77[2] - bbox_77[0]
        
        # Position in the blue/purple area (lower part)
        text_x_77 = size - text_width_77 - int(size * 0.1)  # Right aligned with margin
        text_y_77 = int(size * 0.55)  # Adjust to be in the blue area
        
        # Draw shadow
        draw.text((text_x_77 + shadow_offset, text_y_77 + shadow_offset), text_77, 
                 fill=(0, 0, 0, 128), font=font_77)
        
        # Draw main text
        draw.text((text_x_77, text_y_77), text_77, fill='white', font=font_77)
        
    except Exception as e:
        print(f"Font loading error: {e}")
        # Fallback drawing if fonts fail
        pass
    
    return img

def create_icon_set():
    """Create macOS .icns file with all required sizes"""
    # Required sizes for macOS .icns
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    # Create directory for icons
    os.makedirs('icons', exist_ok=True)
    
    # Generate icons at each size
    for size in sizes:
        icon = create_rainbow_icon(size)
        # Save individual PNG files
        icon.save(f'icons/icon_{size}x{size}.png')
        
        # Also save @2x versions for Retina displays
        if size <= 512:
            icon_2x = create_rainbow_icon(size * 2)
            icon_2x.save(f'icons/icon_{size}x{size}@2x.png')
    
    # Save the largest as the main app icon
    main_icon = create_rainbow_icon(1024)
    main_icon.save('icons/Reel77.png')
    
    print("Rainbow icons created successfully!")
    print("Created the following files:")
    print("- icons/Reel77.png (main icon)")
    for size in sizes:
        print(f"- icons/icon_{size}x{size}.png")
        if size <= 512:
            print(f"- icons/icon_{size}x{size}@2x.png")
    
    print("\nTo create a .icns file for macOS, use:")
    print("cd icons && iconutil -c icns -o Reel77.icns iconset_folder")

if __name__ == "__main__":
    create_icon_set()