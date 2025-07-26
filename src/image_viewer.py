from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QFrame
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot, QSize
from PyQt6.QtGui import QPixmap, QPalette, QColor
from typing import List, Optional
import sys
import random
from functools import partial
sys.path.append('..')
from utils.image_utils import (get_image_files, load_and_scale_image, 
                              get_random_images, calculate_image_dimensions)


class ImageLabel(QLabel):
    """Custom QLabel for displaying images"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                border: 1px solid #222;
                border-radius: 8px;
            }
        """)
        self.setScaledContents(False)
        self._original_pixmap: Optional[QPixmap] = None
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
    def set_image(self, pixmap: QPixmap):
        """Set image while maintaining aspect ratio"""
        if pixmap and not pixmap.isNull():
            self._original_pixmap = pixmap
            self.update_display()
            
    def update_display(self):
        """Update the displayed image"""
        if self._original_pixmap and not self._original_pixmap.isNull():
            # Scale to fit while maintaining aspect ratio
            scaled = self._original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)
            
    def resizeEvent(self, event):
        """Rescale image when label is resized"""
        super().resizeEvent(event)
        if self._original_pixmap and not self._original_pixmap.isNull():
            self.update_display()


class ImageSlot(QFrame):
    """Container for a single image display slot"""
    
    def __init__(self, slot_index: int, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.current_image_path = ""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.image_label = ImageLabel()
        layout.addWidget(self.image_label)
        
        self.setLayout(layout)
        
    def show_image(self, image_path: str, pixmap: QPixmap):
        """Display new image immediately"""
        if not pixmap:
            return
            
        self.current_image_path = image_path
        self.image_label.set_image(pixmap)
        
    def sizeHint(self):
        """Provide size hint to maintain equal sizes"""
        return QSize(300, 600)  # Default size hint


class ImageViewer(QWidget):
    images_changed = pyqtSignal()
    
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.image_files = get_image_files(config['images_dir'])
        self.image_count = config['image_count']
        self.image_slots: List[ImageSlot] = []
        self.timers: List[QTimer] = []
        self.current_images: List[str] = [""] * self.image_count
        self.slot_width = 0
        self.slot_height = 0
        self.init_ui()
        
    def init_ui(self):
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
        self.setPalette(palette)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create image slots
        for i in range(self.image_count):
            slot = ImageSlot(i)
            self.image_slots.append(slot)
            main_layout.addWidget(slot, 1)  # Equal stretch
            
            # Create timer for this slot
            timer = QTimer()
            timer.timeout.connect(partial(self.change_single_image, i))
            self.timers.append(timer)
        
        self.setLayout(main_layout)
        
    def showEvent(self, event):
        """Start display when widget is shown"""
        super().showEvent(event)
        QTimer.singleShot(100, self.start)
        
    def start(self):
        """Start the image display"""
        # Calculate slot dimensions
        self.calculate_slot_dimensions()
        
        available_images = self.image_files.copy()
        random.shuffle(available_images)
        
        # print(f"Starting image viewer with {len(available_images)} images")
        # print(f"Slot dimensions: {self.slot_width}x{self.slot_height}")
        
        # Display initial images
        for i in range(min(self.image_count, len(available_images))):
            self.display_initial_image(i, available_images[i])
            
        # Start timers after a short delay
        for i, timer in enumerate(self.timers):
            QTimer.singleShot(2000 + i * 500, partial(self.start_timer, i))
            
    def calculate_slot_dimensions(self):
        """Calculate dimensions for each slot"""
        # Get available space
        total_width = self.width() - 40 - (15 * (self.image_count - 1))  # Minus margins and spacing
        total_height = self.height() - 40  # Minus margins
        
        # Calculate dimensions for each slot
        self.slot_width = total_width // self.image_count
        self.slot_height = total_height
        
        # Set minimum and maximum sizes for each slot to prevent growing
        for slot in self.image_slots:
            slot.setMinimumWidth(self.slot_width - 10)
            slot.setMaximumWidth(self.slot_width + 10)
            slot.setMinimumHeight(self.slot_height - 10)
            slot.setMaximumHeight(self.slot_height + 10)
            
    def display_initial_image(self, index: int, image_path: str):
        """Display initial image at given index"""
        self.current_images[index] = image_path
        pixmap = self.load_image_for_display(image_path)
        if pixmap:
            self.image_slots[index].show_image(image_path, pixmap)
            
    def start_timer(self, index: int):
        """Start timer for specific slot"""
        interval = random.randint(3000, 5000)  # 3-5 seconds
        self.timers[index].start(interval)
        
    def stop(self):
        """Stop all timers"""
        for timer in self.timers:
            timer.stop()
            
    def load_image_for_display(self, image_path: str) -> Optional[QPixmap]:
        """Load and scale image for slot size"""
        # Use pre-calculated slot dimensions
        img_width = min(self.slot_width, int(self.slot_height * 9 / 16))  # Maintain 9:16 aspect ratio
        img_height = int(img_width * 16 / 9)
        
        return load_and_scale_image(image_path, (img_width, img_height), maintain_aspect=True)
        
    @pyqtSlot()
    def change_single_image(self, index: int):
        """Change a single image at the given index"""
        if index >= len(self.image_slots):
            return
            
        # Get available images
        available = [img for img in self.image_files if img not in self.current_images]
        if not available:
            available = [img for img in self.image_files if img != self.current_images[index]]
            
        if available:
            new_image = random.choice(available)
            self.current_images[index] = new_image
            
            pixmap = self.load_image_for_display(new_image)
            if pixmap:
                self.image_slots[index].show_image(new_image, pixmap)
                self.images_changed.emit()
                
        # Reset timer with new interval
        self.timers[index].stop()
        self.timers[index].start(random.randint(3000, 5000))
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Recalculate dimensions
        if hasattr(self, 'image_slots') and self.image_slots:
            self.calculate_slot_dimensions()