#!/usr/bin/env python3
"""
Create clean rainbow-striped app icon for Reel 77
Optimized for different sizes with appropriate text
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_rainbow_icon(size, use_short_text=False):
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
    
    # Add text based on size
    try:
        # Font paths
        font_paths = [
            '/System/Library/Fonts/Helvetica.ttc',
            '/System/Library/Fonts/HelveticaNeue.ttc',
            '/System/Library/Fonts/Avenir Next.ttc',
            '/Library/Fonts/Arial Bold.ttf',
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf'
        ]
        
        if use_short_text or size < 64:
            # For small icons, use "R77" in a single line
            font_size = int(size * 0.35)
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, font_size, index=1)
                        break
                    except:
                        try:
                            font = ImageFont.truetype(font_path, font_size)
                            break
                        except:
                            continue
            
            if not font:
                font = ImageFont.load_default()
            
            text = "R77"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            text_x = (size - text_width) // 2
            text_y = (size - text_height) // 2
            
            # Draw shadow
            shadow_offset = max(1, size // 256)
            draw.text((text_x + shadow_offset, text_y + shadow_offset), text, 
                     fill=(0, 0, 0, 100), font=font)
            
            # Draw main text
            draw.text((text_x, text_y), text, fill='white', font=font)
            
        else:
            # For larger icons, use "REEL" on top and "77" below
            font_size_reel = int(size * 0.28)
            font_size_77 = int(size * 0.24)
            
            font_reel = None
            font_77 = None
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        if not font_reel:
                            font_reel = ImageFont.truetype(font_path, font_size_reel, index=1)
                        if not font_77:
                            font_77 = ImageFont.truetype(font_path, font_size_77, index=1)
                        break
                    except:
                        try:
                            if not font_reel:
                                font_reel = ImageFont.truetype(font_path, font_size_reel)
                            if not font_77:
                                font_77 = ImageFont.truetype(font_path, font_size_77)
                            break
                        except:
                            continue
            
            if not font_reel:
                font_reel = ImageFont.load_default()
            if not font_77:
                font_77 = font_reel
            
            # Draw "REEL"
            text_reel = "REEL"
            bbox_reel = draw.textbbox((0, 0), text_reel, font=font_reel)
            text_width_reel = bbox_reel[2] - bbox_reel[0]
            text_height_reel = bbox_reel[3] - bbox_reel[1]
            
            # Draw "77"
            text_77 = "77"
            bbox_77 = draw.textbbox((0, 0), text_77, font=font_77)
            text_width_77 = bbox_77[2] - bbox_77[0]
            text_height_77 = bbox_77[3] - bbox_77[1]
            
            # Calculate vertical spacing
            total_height = text_height_reel + text_height_77 + int(size * 0.05)  # Small gap
            start_y = (size - total_height) // 2
            
            # Position REEL
            text_x_reel = (size - text_width_reel) // 2
            text_y_reel = start_y
            
            # Position 77
            text_x_77 = (size - text_width_77) // 2
            text_y_77 = start_y + text_height_reel + int(size * 0.05)
            
            # Draw shadows
            shadow_offset = max(1, size // 128)
            draw.text((text_x_reel + shadow_offset, text_y_reel + shadow_offset), text_reel, 
                     fill=(0, 0, 0, 100), font=font_reel)
            draw.text((text_x_77 + shadow_offset, text_y_77 + shadow_offset), text_77, 
                     fill=(0, 0, 0, 100), font=font_77)
            
            # Draw main text
            draw.text((text_x_reel, text_y_reel), text_reel, fill='white', font=font_reel)
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
        # Use short text for small icons
        use_short = size <= 32
        icon = create_rainbow_icon(size, use_short_text=use_short)
        # Save individual PNG files
        icon.save(f'icons/icon_{size}x{size}.png')
        
        # Also save @2x versions for Retina displays
        if size <= 512:
            icon_2x = create_rainbow_icon(size * 2, use_short_text=use_short)
            icon_2x.save(f'icons/icon_{size}x{size}@2x.png')
    
    # Save the largest as the main app icon
    main_icon = create_rainbow_icon(1024)
    main_icon.save('icons/Reel77.png')
    
    # Also create a smaller version for dock/menu use
    dock_icon = create_rainbow_icon(256)
    dock_icon.save('icons/Reel77_dock.png')
    
    print("Clean rainbow icons created successfully!")
    print("Created the following files:")
    print("- icons/Reel77.png (main icon)")
    print("- icons/Reel77_dock.png (dock-sized icon)")
    for size in sizes:
        print(f"- icons/icon_{size}x{size}.png")
        if size <= 512:
            print(f"- icons/icon_{size}x{size}@2x.png")
    
    print("\nSmall icons (16x16, 32x32) use 'R77' text")
    print("Larger icons use 'REEL' over '77' layout")

if __name__ == "__main__":
    create_icon_set()