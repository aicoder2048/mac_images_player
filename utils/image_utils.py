import os
import random
from typing import List, Tuple, Optional
from PIL import Image, ImageOps
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt


def get_image_files(directory: str) -> List[str]:
    """Get all image files from a directory"""
    # Note: .gif might have issues with animations, only first frame will be shown
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
    image_files = []
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(fmt) for fmt in supported_formats):
            image_files.append(os.path.join(directory, file))
            
    return image_files


def load_and_scale_image(image_path: str, target_size: Tuple[int, int], 
                        maintain_aspect: bool = True) -> Optional[QPixmap]:
    """Load an image and scale it to target size"""
    try:
        # Load image with PIL first for better format support
        pil_image = Image.open(image_path)
        
        # Handle EXIF orientation for JPEG images
        try:
            pil_image = ImageOps.exif_transpose(pil_image)
        except:
            # If EXIF handling fails, continue with original image
            pass
        
        # Handle different image modes
        if pil_image.mode == 'RGBA':
            # Keep RGBA
            pil_image = pil_image.convert('RGBA')
            bytes_per_line = 4 * pil_image.width
            qimage_format = QImage.Format.Format_RGBA8888
        elif pil_image.mode in ('LA', 'PA'):
            # Convert grayscale with alpha to RGBA
            pil_image = pil_image.convert('RGBA')
            bytes_per_line = 4 * pil_image.width
            qimage_format = QImage.Format.Format_RGBA8888
        elif pil_image.mode == 'P':
            # Convert palette images to RGBA to preserve transparency if any
            if 'transparency' in pil_image.info:
                pil_image = pil_image.convert('RGBA')
                bytes_per_line = 4 * pil_image.width
                qimage_format = QImage.Format.Format_RGBA8888
            else:
                pil_image = pil_image.convert('RGB')
                bytes_per_line = 3 * pil_image.width
                qimage_format = QImage.Format.Format_RGB888
        else:
            # Convert everything else to RGB (including L, 1, CMYK, etc.)
            pil_image = pil_image.convert('RGB')
            bytes_per_line = 3 * pil_image.width
            qimage_format = QImage.Format.Format_RGB888
            
        # Get image data and create QImage with proper byte alignment
        img_data = pil_image.tobytes()
        
        # Create QImage with explicit bytes per line for proper alignment
        qimage = QImage(img_data, pil_image.width, pil_image.height, 
                       bytes_per_line, qimage_format)
        
        # Make a copy to ensure data persistence
        qimage = qimage.copy()
        
        # Convert to pixmap
        pixmap = QPixmap.fromImage(qimage)
        
        # Scale to target size
        if maintain_aspect:
            pixmap = pixmap.scaled(
                target_size[0], target_size[1],
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            pixmap = pixmap.scaled(
                target_size[0], target_size[1],
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
        return pixmap
        
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def get_random_images(image_files: List[str], count: int) -> List[str]:
    """Get random images from the list"""
    if len(image_files) <= count:
        return image_files.copy()
    return random.sample(image_files, count)


def calculate_image_dimensions(screen_width: int, screen_height: int, 
                             image_count: int, padding: int = 20) -> Tuple[int, int]:
    """Calculate optimal dimensions for each image based on screen size and count"""
    # Account for padding between images and screen edges
    total_padding = padding * (image_count + 1)
    available_width = screen_width - total_padding
    
    # Calculate width per image
    image_width = available_width // image_count
    
    # For 9:16 aspect ratio
    image_height = int(image_width * 16 / 9)
    
    # Check if height fits on screen
    if image_height > screen_height - (padding * 2):
        image_height = screen_height - (padding * 2)
        image_width = int(image_height * 9 / 16)
        
    return image_width, image_height