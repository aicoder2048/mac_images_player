from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QFrame, QGraphicsOpacityEffect, QGraphicsBlurEffect
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPalette, QColor, QTransform, QPainter, QFont, QPen, QBrush
from typing import List, Optional
from enum import Enum
import sys
import random
from functools import partial
sys.path.append('..')
from utils.image_utils import (get_image_files, load_and_scale_image, 
                              get_random_images, calculate_image_dimensions)


class DisplayMode(Enum):
    FIT = "Fit"  # Original mode with black bars
    BLUR_FILL = "Blur Fill"  # Mode with blurred background
    ZOOM_FILL = "Zoom Fill"  # Zoom to fill entire pane


class ImageLabel(QLabel):
    """Custom QLabel for displaying images with different display modes"""
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
        self._background_pixmap: Optional[QPixmap] = None
        self._display_mode = DisplayMode.BLUR_FILL  # Default to blur fill
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        
    def set_image(self, pixmap: QPixmap):
        """Set image while maintaining aspect ratio"""
        if pixmap and not pixmap.isNull():
            self._original_pixmap = pixmap
            self.update_display()
            
    def set_display_mode(self, mode: DisplayMode):
        """Set the display mode and update the display"""
        if self._display_mode != mode:
            self._display_mode = mode
            self.update_display()
            
    def create_blurred_background(self, pixmap: QPixmap) -> QPixmap:
        """Create a blurred version of the image for background"""
        # Scale image to fill the entire label (may crop)
        scaled_fill = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Crop to exact size if needed
        if scaled_fill.size() != self.size():
            x = (scaled_fill.width() - self.width()) // 2
            y = (scaled_fill.height() - self.height()) // 2
            scaled_fill = scaled_fill.copy(x, y, self.width(), self.height())
        
        # Simple blur: scale down then up
        small_size = QSize(max(1, self.width() // 8), max(1, self.height() // 8))
        blurred = scaled_fill.scaled(small_size, Qt.AspectRatioMode.IgnoreAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        blurred = blurred.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        
        # Add a dark overlay for better contrast
        painter = QPainter(blurred)
        painter.fillRect(blurred.rect(), QColor(0, 0, 0, 120))
        painter.end()
        
        return blurred
            
    def update_display(self):
        """Update the displayed image based on current display mode"""
        if self._original_pixmap and not self._original_pixmap.isNull():
            if self._display_mode == DisplayMode.FIT:
                # Original fit mode - just scale and center with black bars
                scaled = self._original_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                super().setPixmap(scaled)
                
            elif self._display_mode == DisplayMode.BLUR_FILL:
                # Blur fill mode - blurred background with centered image
                display_pixmap = QPixmap(self.size())
                display_pixmap.fill(QColor(10, 10, 10))
                
                painter = QPainter(display_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # Draw blurred background
                blurred_bg = self.create_blurred_background(self._original_pixmap)
                painter.drawPixmap(0, 0, blurred_bg)
                
                # Draw the main image on top
                scaled = self._original_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Center the image
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
                
                painter.end()
                
                super().setPixmap(display_pixmap)
                
            elif self._display_mode == DisplayMode.ZOOM_FILL:
                # Zoom fill mode - scale to fill and crop
                scaled = self._original_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Crop to exact size if needed
                if scaled.size() != self.size():
                    x = (scaled.width() - self.width()) // 2
                    y = (scaled.height() - self.height()) // 2
                    scaled = scaled.copy(x, y, self.width(), self.height())
                
                super().setPixmap(scaled)
            
    def resizeEvent(self, event):
        """Rescale image when label is resized"""
        super().resizeEvent(event)
        if self._original_pixmap and not self._original_pixmap.isNull():
            self.update_display()
            
    def clear(self):
        """Clear the label"""
        super().clear()
        self._original_pixmap = None
        self._background_pixmap = None


class ImageSlot(QFrame):
    """Container for a single image display slot"""
    
    clicked = pyqtSignal(int)  # Signal when clicked, sends slot index
    
    def __init__(self, slot_index: int, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.current_image_path = ""
        self.is_transitioning = False
        self.is_pinned = False
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create two labels for smooth transitions
        self.current_label = ImageLabel()
        self.next_label = ImageLabel()
        self.next_label.hide()
        
        # Stack them on top of each other
        self.current_label.setParent(self)
        self.next_label.setParent(self)
        
        
        # Set up opacity effects
        self.current_opacity = QGraphicsOpacityEffect()
        self.next_opacity = QGraphicsOpacityEffect()
        self.current_label.setGraphicsEffect(self.current_opacity)
        self.next_label.setGraphicsEffect(self.next_opacity)
        
        layout.addWidget(self.current_label)
        
        # Create pin icon label (overlay)
        self.pin_label = QLabel(self)
        self.pin_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border-radius: 20px;
                padding: 8px;
                font-size: 24px;
            }
        """)
        self.pin_label.setText("📌")
        self.pin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_label.setFixedSize(40, 40)
        self.pin_label.hide()
        self.pin_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        self.setLayout(layout)
        
    def show_image(self, image_path: str, pixmap: QPixmap, initial=False):
        """Display new image with optional transition"""
        if not pixmap or self.is_transitioning:
            return
            
        self.current_image_path = image_path
        
        if initial:
            # Initial load - no animation
            self.current_label.set_image(pixmap)
            self.current_opacity.setOpacity(1.0)
        else:
            # Animate transition with random effect
            self.is_transitioning = True
            effect_type = random.choice(['fade', 'fade_rotate'])
            
            if effect_type == 'fade':
                self.simple_fade_transition(pixmap)
            else:
                self.fade_rotate_transition(pixmap)
                
    def simple_fade_transition(self, pixmap: QPixmap):
        """Simple fade transition"""
        # Set new image on next label
        self.next_label.set_image(pixmap)
        self.next_label.move(self.current_label.pos())
        self.next_label.resize(self.current_label.size())
        self.next_label.show()
        
        # Create fade animations
        fade_out = QPropertyAnimation(self.current_opacity, b"opacity")
        fade_out.setDuration(800)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        
        fade_in = QPropertyAnimation(self.next_opacity, b"opacity")
        fade_in.setDuration(800)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        
        # Parallel animation
        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(fade_out)
        self.anim_group.addAnimation(fade_in)
        self.anim_group.finished.connect(self.on_transition_complete)
        self.anim_group.start()
        
    def fade_rotate_transition(self, pixmap: QPixmap):
        """Fade with slight rotation effect"""
        # For safety, just do a simple fade to avoid breaking display
        self.simple_fade_transition(pixmap)
        
    def on_transition_complete(self):
        """Handle transition completion"""
        # Swap labels
        self.current_label, self.next_label = self.next_label, self.current_label
        self.current_opacity, self.next_opacity = self.next_opacity, self.current_opacity
        
        # Hide the old label
        self.next_label.hide()
        self.next_opacity.setOpacity(0.0)
        
        self.is_transitioning = False
        
    def resizeEvent(self, event):
        """Handle resize to keep labels aligned"""
        super().resizeEvent(event)
        # Make sure both labels fill the slot
        rect = self.rect()
        self.current_label.setGeometry(rect)
        self.next_label.setGeometry(rect)
        # Position pin label in top-right corner
        self.pin_label.move(rect.width() - 50, 10)
        
    def sizeHint(self):
        """Provide size hint to maintain equal sizes"""
        return QSize(300, 600)  # Default size hint
        
    def mousePressEvent(self, event):
        """Handle mouse clicks to toggle pin state"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.slot_index)
            
    def set_pinned(self, pinned: bool):
        """Set the pinned state and update visual indicator"""
        self.is_pinned = pinned
        if pinned:
            self.pin_label.show()
        else:
            self.pin_label.hide()
            
    def set_display_mode(self, mode: DisplayMode):
        """Set display mode for both labels"""
        self.current_label.set_display_mode(mode)
        self.next_label.set_display_mode(mode)


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
        self.is_paused = False
        self.pause_label = None
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
            slot.clicked.connect(self.toggle_pin)  # Connect click signal
            self.image_slots.append(slot)
            main_layout.addWidget(slot, 1)  # Equal stretch
            
            # Create timer for this slot
            timer = QTimer()
            timer.timeout.connect(partial(self.change_single_image, i))
            self.timers.append(timer)
        
        self.setLayout(main_layout)
        
        # Create single pause indicator (floating)
        self.pause_label = QLabel(self)
        self.pause_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                font-size: 36px;
                font-weight: bold;
                padding: 15px 25px;
                border-radius: 10px;
            }
        """)
        self.pause_label.setText("⏸ PAUSED")
        self.pause_label.hide()
        
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
        
        # Display initial images
        for i in range(min(self.image_count, len(available_images))):
            self.display_initial_image(i, available_images[i])
            
        # Start all timers immediately with different intervals
        for i in range(len(self.timers)):
            if i == 0:
                # First timer starts with 2 second interval
                self.timers[0].start(2000)
            else:
                # Other timers start with random 3-5 second intervals
                interval = random.randint(3000, 5000)
                self.timers[i].start(interval)
            
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
            self.image_slots[index].show_image(image_path, pixmap, initial=True)
            
    def start_timer(self, index: int):
        """Start timer for specific slot"""
        # Simple random interval between 3-5 seconds
        interval = random.randint(3000, 5000)
        self.timers[index].start(interval)
        
    def stop(self):
        """Stop all timers"""
        for timer in self.timers:
            timer.stop()
            
    def pause(self):
        """Pause all image changes"""
        if not self.is_paused:
            self.is_paused = True
            # Stop all timers
            for timer in self.timers:
                if timer.isActive():
                    timer.stop()
            # Show pause indicator
            self.pause_label.show()
            self.position_pause_label()
                    
    def resume(self):
        """Resume all image changes"""
        if self.is_paused:
            self.is_paused = False
            # Hide pause indicator
            self.pause_label.hide()
            # Restart timers with random intervals
            for i in range(len(self.timers)):
                interval = random.randint(3000, 5000)
                self.timers[i].start(interval)
                
    def position_pause_label(self):
        """Position pause label in center of viewer"""
        if self.pause_label:
            self.pause_label.adjustSize()
            x = (self.width() - self.pause_label.width()) // 2
            y = self.height() - self.pause_label.height() - 50
            self.pause_label.move(x, y)
            
    def load_image_for_display(self, image_path: str) -> Optional[QPixmap]:
        """Load and scale image for slot size"""
        # Use full slot dimensions to maximize image size
        return load_and_scale_image(image_path, (self.slot_width, self.slot_height), maintain_aspect=True)
        
    @pyqtSlot()
    def change_single_image(self, index: int):
        """Change a single image at the given index"""
        if index >= len(self.image_slots):
            return
            
        # Skip if this slot is pinned
        if self.image_slots[index].is_pinned:
            # Keep the timer running but don't change the image
            self.timers[index].stop()
            self.timers[index].start(random.randint(3000, 5000))
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
                self.image_slots[index].show_image(new_image, pixmap, initial=False)
                self.images_changed.emit()
                
        # Reset timer with new random interval
        self.timers[index].stop()
        interval = random.randint(3000, 5000)
        self.timers[index].start(interval)
        
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Recalculate dimensions
        if hasattr(self, 'image_slots') and self.image_slots:
            self.calculate_slot_dimensions()
        # Reposition pause label if visible
        if self.is_paused and self.pause_label:
            self.position_pause_label()
            
    @pyqtSlot(int)
    def toggle_pin(self, slot_index: int):
        """Toggle pin state for a slot"""
        if slot_index < len(self.image_slots):
            slot = self.image_slots[slot_index]
            slot.set_pinned(not slot.is_pinned)
            
    def set_display_mode(self, mode: DisplayMode):
        """Set display mode for all image slots"""
        for slot in self.image_slots:
            slot.set_display_mode(mode)