from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QFrame, QGraphicsOpacityEffect, QGraphicsBlurEffect, QStackedLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPalette, QColor, QTransform, QPainter, QFont, QPen, QBrush, QImage
from typing import List, Optional, Tuple
from enum import Enum
import sys
import random
import time
import os
from functools import partial
from PIL import Image
sys.path.append('..')
from utils.image_utils import (get_image_files, get_image_files_from_dirs, 
                              load_and_scale_image, get_random_images, 
                              calculate_image_dimensions)


class DisplayMode(Enum):
    FIT = "Fit"  # Original mode with black bars
    BLUR_FILL = "Blur Fill"  # Mode with blurred background
    ZOOM_FILL = "Zoom Fill"  # Zoom to fill entire pane


class LayoutMode(Enum):
    PORTRAIT = "portrait"  # Multiple vertical columns
    LANDSCAPE = "landscape"  # Single horizontal row


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
        
    def show_image(self, image_path: str, pixmap: QPixmap, initial=False, fast_transition=False):
        """Display new image with optional transition"""
        if not pixmap:
            return
            
        if self.is_transitioning:
            print(f"[DEBUG] Image dropped during transition: {os.path.basename(image_path)}")
            return
            
        self.current_image_path = image_path
        
        if initial:
            # Initial load - no animation
            self.current_label.set_image(pixmap)
            self.current_opacity.setOpacity(1.0)
        else:
            # Animate transition with random effect
            self.is_transitioning = True
            self.fast_transition = fast_transition
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
        
        # Use faster animation for landscape mode
        duration = 400 if hasattr(self, 'fast_transition') and self.fast_transition else 800
        
        # Create fade animations
        fade_out = QPropertyAnimation(self.current_opacity, b"opacity")
        fade_out.setDuration(duration)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        
        fade_in = QPropertyAnimation(self.next_opacity, b"opacity")
        fade_in.setDuration(duration)
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
        # Handle both old single-dir and new multi-dir configs
        if 'images_dirs' in config:
            self.image_files = get_image_files_from_dirs(config['images_dirs'])
        else:
            # Fallback for old config format
            self.image_files = get_image_files(config.get('images_dir', ''))
        self.image_count = config['image_count']
        
        # Store timing configurations with defaults
        self.portrait_timing = config.get('portrait_timing', '3-5 seconds')
        self.landscape_timing = config.get('landscape_timing', '2-4 seconds')
        self.image_slots: List[ImageSlot] = []
        self.timers: List[QTimer] = []
        self.current_images: List[str] = [""] * self.image_count
        self.slot_width = 0
        self.slot_height = 0
        self.is_paused = False
        self.pause_label = None
        
        # Layout mode tracking
        self.current_layout_mode = LayoutMode.PORTRAIT
        self.transition_in_progress = False
        self.mode_switch_cooldown = QTimer()
        self.mode_switch_cooldown.setSingleShot(True)
        self.mode_switch_cooldown.timeout.connect(self.on_cooldown_finished)
        self.cooldown_duration = 3000  # 3 seconds minimum between mode switches
        
        # Image categorization
        self.portrait_images: List[str] = []
        self.landscape_images: List[str] = []
        self.categorize_images()
        
        # Landscape mode components (will be created in init_ui)
        self.landscape_slot: Optional[ImageSlot] = None
        self.landscape_timer: Optional[QTimer] = None
        self.landscape_width = 0
        self.landscape_height = 0
        self.landscape_image_count = 0  # Track how many landscape images shown
        self.landscape_start_time = 0  # Track when landscape mode started
        self.last_landscape_change_time = 0  # Track time between changes
        
        # Timer state preservation for better UX
        self.portrait_timer_states: List[dict] = []  # Store timer states during landscape mode
        self.landscape_source_slot_index = -1  # Track which slot triggered landscape mode
        
        self.init_ui()
        
    def parse_timing_range(self, timing_string: str) -> Tuple[int, int]:
        """Parse timing string to millisecond range tuple"""
        timing_map = {
            "2-4 seconds": (2000, 4000),
            "3-5 seconds": (3000, 5000), 
            "4-6 seconds": (4000, 6000),
            "5-7 seconds": (5000, 7000),
            "6-8 seconds": (6000, 8000)
        }
        return timing_map.get(timing_string, (3000, 5000))  # Default fallback
        
    def get_portrait_timing_range(self) -> Tuple[int, int]:
        """Get portrait timing range in milliseconds"""
        return self.parse_timing_range(self.portrait_timing)
        
    def get_landscape_timing_range(self) -> Tuple[int, int]:
        """Get landscape timing range in milliseconds"""
        return self.parse_timing_range(self.landscape_timing)
        
    def get_random_portrait_interval(self) -> int:
        """Get random interval for portrait mode"""
        min_ms, max_ms = self.get_portrait_timing_range()
        return random.randint(min_ms, max_ms)
        
    def get_random_landscape_interval(self) -> int:
        """Get random interval for landscape mode"""
        min_ms, max_ms = self.get_landscape_timing_range()
        return random.randint(min_ms, max_ms)
        
    def init_ui(self):
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
        self.setPalette(palette)
        
        # Create stacked layout for switching between portrait and landscape modes
        self.stacked_layout = QStackedLayout()
        
        # Create portrait mode widget
        self.portrait_widget = QWidget()
        portrait_layout = QHBoxLayout()
        portrait_layout.setContentsMargins(20, 20, 20, 20)
        portrait_layout.setSpacing(15)
        
        # Create image slots for portrait mode
        for i in range(self.image_count):
            slot = ImageSlot(i)
            slot.clicked.connect(self.toggle_pin)  # Connect click signal
            self.image_slots.append(slot)
            portrait_layout.addWidget(slot, 1)  # Equal stretch
            
            # Create timer for this slot
            timer = QTimer()
            timer.timeout.connect(partial(self.change_single_image, i))
            self.timers.append(timer)
        
        self.portrait_widget.setLayout(portrait_layout)
        
        # Create landscape mode widget
        self.landscape_widget = QWidget()
        landscape_layout = QVBoxLayout()
        landscape_layout.setContentsMargins(20, 20, 20, 20)
        landscape_layout.setSpacing(0)
        
        # Create single slot for landscape mode
        self.landscape_slot = ImageSlot(99)  # Use 99 as special index for landscape
        self.landscape_slot.clicked.connect(lambda: self.toggle_pin_landscape())
        landscape_layout.addWidget(self.landscape_slot)
        
        # Create timer for landscape slot
        self.landscape_timer = QTimer()
        # Don't connect anything initially - will be connected when entering landscape mode
        
        self.landscape_widget.setLayout(landscape_layout)
        
        # Add both widgets to stacked layout
        self.stacked_layout.addWidget(self.portrait_widget)
        self.stacked_layout.addWidget(self.landscape_widget)
        
        # Start with portrait mode
        self.stacked_layout.setCurrentWidget(self.portrait_widget)
        
        self.setLayout(self.stacked_layout)
        
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
        
        # Start with random selection from ALL images
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
                # Other timers start with random portrait intervals
                interval = self.get_random_portrait_interval()
                self.timers[i].start(interval)
            
    def calculate_slot_dimensions(self):
        """Calculate dimensions for each slot based on current mode"""
        if self.current_layout_mode == LayoutMode.PORTRAIT:
            # Get available space for portrait mode
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
        else:
            # Landscape mode - use full width and height
            self.landscape_width = self.width() - 40
            self.landscape_height = self.height() - 40
            
            if self.landscape_slot:
                self.landscape_slot.setMinimumWidth(self.landscape_width - 10)
                self.landscape_slot.setMaximumWidth(self.landscape_width + 10)
                self.landscape_slot.setMinimumHeight(self.landscape_height - 10)
                self.landscape_slot.setMaximumHeight(self.landscape_height + 10)
            
    def display_initial_image(self, index: int, image_path: str):
        """Display initial image at given index"""
        self.current_images[index] = image_path
        pixmap = self.load_image_for_display(image_path)
        if pixmap:
            self.image_slots[index].show_image(image_path, pixmap, initial=True)
            
    def start_timer(self, index: int):
        """Start timer for specific slot"""
        # Use portrait timing for individual slots
        interval = self.get_random_portrait_interval()
        self.timers[index].start(interval)
        
    def stop(self):
        """Stop all timers"""
        for timer in self.timers:
            timer.stop()
            
    def pause(self):
        """Pause all image changes"""
        if not self.is_paused:
            self.is_paused = True
            # Stop all timers based on current mode
            if self.current_layout_mode == LayoutMode.PORTRAIT:
                for timer in self.timers:
                    if timer.isActive():
                        timer.stop()
            else:
                if self.landscape_timer.isActive():
                    self.landscape_timer.stop()
            # Show pause indicator
            self.pause_label.show()
            self.position_pause_label()
                    
    def resume(self):
        """Resume all image changes"""
        if self.is_paused:
            self.is_paused = False
            # Hide pause indicator
            self.pause_label.hide()
            # Restart timers based on current mode
            if self.current_layout_mode == LayoutMode.PORTRAIT:
                for i in range(len(self.timers)):
                    interval = self.get_random_portrait_interval()
                    self.timers[i].start(interval)
            else:
                interval = self.get_random_landscape_interval()
                self.landscape_timer.start(interval)
                
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
            self.timers[index].start(self.get_random_portrait_interval())
            return
            
        # Get available images from ALL images (not just portrait)
        available = [img for img in self.image_files if img not in self.current_images]
        if not available:
            available = [img for img in self.image_files if img != self.current_images[index]]
            
        if available:
            new_image = random.choice(available)
            self.current_images[index] = new_image
            
            # Check if this is a landscape image and we should switch modes
            if self.current_layout_mode == LayoutMode.PORTRAIT:
                try:
                    with Image.open(new_image) as img:
                        width, height = img.size
                        if width > height and not self.transition_in_progress:
                            # This is a landscape image, switch to landscape mode
                            self.switch_to_landscape_mode_with_image(new_image, index)
                            return
                except Exception as e:
                    print(f"Error checking image orientation: {e}")
            
            pixmap = self.load_image_for_display(new_image)
            if pixmap:
                self.image_slots[index].show_image(new_image, pixmap, initial=False)
                self.images_changed.emit()
                
        # Reset timer with new random interval
        self.timers[index].stop()
        interval = self.get_random_portrait_interval()
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
        if self.landscape_slot:
            self.landscape_slot.set_display_mode(mode)
            
    def categorize_images(self):
        """Categorize images by orientation"""
        for img_path in self.image_files:
            try:
                # Use PIL to get image dimensions without loading full image
                with Image.open(img_path) as img:
                    width, height = img.size
                    if width > height:
                        self.landscape_images.append(img_path)
                    else:
                        self.portrait_images.append(img_path)
            except Exception as e:
                print(f"Error checking image {img_path}: {e}")
                # Assume portrait if can't determine
                self.portrait_images.append(img_path)
                
        print(f"Total images: {len(self.image_files)} ({len(self.portrait_images)} portrait, {len(self.landscape_images)} landscape)")
        print("Using true random selection from all images")
        
        # Show source directories info
        if 'images_dirs' in self.config:
            print(f"Images loaded from {len(self.config['images_dirs'])} directories:")
            for dir_path in self.config['images_dirs']:
                dir_count = len([f for f in self.image_files if f.startswith(dir_path)])
                print(f"  - {dir_path}: {dir_count} images")
        
    def on_cooldown_finished(self):
        """Called when mode switch cooldown expires"""
        # Cooldown finished, mode switches are now allowed
        pass
        
    def toggle_pin_landscape(self):
        """Toggle pin state for landscape slot"""
        if self.landscape_slot:
            self.landscape_slot.set_pinned(not self.landscape_slot.is_pinned)
            
    def change_landscape_image(self):
        """Called when landscape timer expires - always return to portrait mode"""
        current_time = time.time()
        if self.last_landscape_change_time > 0:
            time_since_last = current_time - self.last_landscape_change_time
            print(f"[DEBUG] Landscape timer expired at {current_time:.2f}, {time_since_last:.2f}s since image shown")
        
        # Check if landscape image is pinned
        if self.landscape_slot.is_pinned:
            print("[DEBUG] Landscape image is pinned, staying in landscape mode")
            # Restart timer to check again later
            self.landscape_timer.setSingleShot(True)
            interval = self.get_random_landscape_interval()
            print(f"[DEBUG] Restarting timer with interval: {interval}ms")
            self.landscape_timer.start(interval)
            return
        
        # Always switch back to portrait mode after showing a landscape image
        print("[DEBUG] Landscape display complete, returning to portrait mode")
        self.switch_to_portrait_mode()
            
    def load_landscape_image(self, image_path: str) -> Optional[QPixmap]:
        """Load and scale landscape image"""
        return load_and_scale_image(image_path, (self.landscape_width, self.landscape_height), maintain_aspect=True)
        
    def debug_timer_status(self):
        """Debug timer status"""
        if hasattr(self, 'landscape_timer'):
            print(f"[DEBUG TIMER] Landscape timer active: {self.landscape_timer.isActive()}")
            print(f"[DEBUG TIMER] Landscape timer interval: {self.landscape_timer.interval()}")
            print(f"[DEBUG TIMER] Current layout mode: {self.current_layout_mode}")
            print(f"[DEBUG TIMER] Is paused: {self.is_paused}")
        
        
    def switch_to_landscape_mode_with_image(self, image_path: str, source_slot_index: int = -1):
        """Switch to landscape mode and display the specified image"""
        if self.transition_in_progress or self.current_layout_mode == LayoutMode.LANDSCAPE:
            return
            
        self.transition_in_progress = True
        self.landscape_source_slot_index = source_slot_index
        
        # Save portrait timer states before stopping them
        self.portrait_timer_states = []
        for i, timer in enumerate(self.timers):
            remaining_time = timer.remainingTime() if timer.isActive() else 0
            self.portrait_timer_states.append({
                'index': i,
                'remaining': max(remaining_time, 1000),  # Minimum 1 second
                'was_active': timer.isActive(),
                'current_image': self.current_images[i] if i < len(self.current_images) else ""
            })
            timer.stop()
            
        print(f"[DEBUG] Saved portrait timer states: {[(s['index'], s['remaining'], s['was_active']) for s in self.portrait_timer_states]}")
        
        # Start progressive transition animation before switching layout
        if source_slot_index >= 0 and source_slot_index < len(self.image_slots):
            self.start_landscape_transition_animation(image_path, source_slot_index)
        else:
            # Fallback to immediate switch if source slot is invalid
            self.complete_landscape_transition(image_path)
            
    def start_landscape_transition_animation(self, image_path: str, source_slot_index: int):
        """Start progressive transition from portrait slot to landscape mode"""
        # First, show the landscape image in the source slot
        pixmap = self.load_image_for_display(image_path)
        if pixmap:
            self.image_slots[source_slot_index].show_image(image_path, pixmap, initial=False, fast_transition=True)
        
        # Create opacity effects for non-source slots
        self.transition_opacity_effects = []
        for i, slot in enumerate(self.image_slots):
            if i != source_slot_index:
                opacity_effect = QGraphicsOpacityEffect()
                opacity_effect.setOpacity(1.0)
                slot.setGraphicsEffect(opacity_effect)
                self.transition_opacity_effects.append((i, opacity_effect))
        
        # Create fade out animation for non-source slots
        self.fade_out_animations = QParallelAnimationGroup()
        for i, opacity_effect in self.transition_opacity_effects:
            fade_anim = QPropertyAnimation(opacity_effect, b"opacity")
            fade_anim.setDuration(800)  # 800ms fade out
            fade_anim.setStartValue(1.0)
            fade_anim.setEndValue(0.1)  # Fade to 10% opacity instead of completely hiding
            self.fade_out_animations.addAnimation(fade_anim)
        
        # Connect animation completion to layout switch
        self.fade_out_animations.finished.connect(lambda: self.complete_landscape_transition(image_path))
        self.fade_out_animations.start()
        
    def complete_landscape_transition(self, image_path: str):
        """Complete the transition to landscape mode"""
        # Switch layout
        self.current_layout_mode = LayoutMode.LANDSCAPE
        self.stacked_layout.setCurrentWidget(self.landscape_widget)
        
        # Calculate landscape dimensions
        self.calculate_slot_dimensions()
        
        # Reset landscape tracking
        self.landscape_image_count = 0
        self.landscape_start_time = time.time()
        self.last_landscape_change_time = self.landscape_start_time
        
        # Display the specified landscape image
        pixmap = self.load_landscape_image(image_path)
        if pixmap:
            self.landscape_slot.show_image(image_path, pixmap, initial=True)
            self.landscape_image_count = 1
                
        # Start a single-shot timer to switch back to portrait after showing this landscape image
        try:
            self.landscape_timer.timeout.disconnect()
        except:
            pass  # No connections to disconnect
        self.landscape_timer.timeout.connect(self.change_landscape_image)
        self.landscape_timer.setSingleShot(True)  # Single shot - only fire once
        interval = self.get_random_landscape_interval()
        self.landscape_timer.start(interval)
        
        # Start cooldown
        self.mode_switch_cooldown.start(self.cooldown_duration)
        
        self.transition_in_progress = False
        
    def switch_to_landscape_mode(self):
        """Switch from portrait to landscape mode"""
        if self.transition_in_progress or self.current_layout_mode == LayoutMode.LANDSCAPE:
            return
            
        self.transition_in_progress = True
        
        # Stop all portrait timers
        for timer in self.timers:
            timer.stop()
            
        # TODO: Add fade out animation here
        
        # Switch layout
        self.current_layout_mode = LayoutMode.LANDSCAPE
        self.stacked_layout.setCurrentWidget(self.landscape_widget)
        
        # Calculate landscape dimensions
        self.calculate_slot_dimensions()
        
        # Reset landscape tracking
        self.landscape_image_count = 0
        self.landscape_start_time = time.time()
        self.last_landscape_change_time = self.landscape_start_time
        
        # Load and display a landscape image
        if self.landscape_images:
            image_path = random.choice(self.landscape_images)
            print(f"[DEBUG] Initial landscape image: {os.path.basename(image_path)}")
            pixmap = self.load_landscape_image(image_path)
            if pixmap:
                self.landscape_slot.show_image(image_path, pixmap, initial=True)
                self.landscape_image_count = 1
                
        # Start a single-shot timer to switch back to portrait after showing this landscape image
        try:
            self.landscape_timer.timeout.disconnect()
        except:
            pass  # No connections to disconnect
        self.landscape_timer.timeout.connect(self.change_landscape_image)
        self.landscape_timer.setSingleShot(True)  # Single shot - only fire once
        interval = self.get_random_landscape_interval()
        print(f"[DEBUG] Starting landscape timer with interval: {interval}ms (will switch to portrait after)")
        self.landscape_timer.start(interval)
        print(f"[DEBUG] Timer started successfully: {self.landscape_timer.isActive()}, single shot: {self.landscape_timer.isSingleShot()}")
        
        # Start cooldown
        self.mode_switch_cooldown.start(self.cooldown_duration)
        
        self.transition_in_progress = False
        
    def switch_to_portrait_mode(self):
        """Switch from landscape to portrait mode"""
        if self.transition_in_progress or self.current_layout_mode == LayoutMode.PORTRAIT:
            return
            
        self.transition_in_progress = True
        
        # Stop landscape timer
        self.landscape_timer.stop()
        
        # Start progressive transition animation from landscape to portrait
        self.start_portrait_transition_animation()
        
    def start_portrait_transition_animation(self):
        """Start progressive transition from landscape to portrait mode"""
        # Create fade out effect for landscape widget
        self.landscape_fade_effect = QGraphicsOpacityEffect()
        self.landscape_fade_effect.setOpacity(1.0)
        self.landscape_widget.setGraphicsEffect(self.landscape_fade_effect)
        
        # Create fade out animation for landscape
        self.landscape_fade_animation = QPropertyAnimation(self.landscape_fade_effect, b"opacity")
        self.landscape_fade_animation.setDuration(600)  # 600ms fade out
        self.landscape_fade_animation.setStartValue(1.0)
        self.landscape_fade_animation.setEndValue(0.0)
        
        # Connect animation completion to layout switch
        self.landscape_fade_animation.finished.connect(self.complete_portrait_transition)
        self.landscape_fade_animation.start()
        
    def complete_portrait_transition(self):
        """Complete the transition to portrait mode"""
        # Switch layout
        self.current_layout_mode = LayoutMode.PORTRAIT
        self.stacked_layout.setCurrentWidget(self.portrait_widget)
        
        # Calculate portrait dimensions
        self.calculate_slot_dimensions()
        
        # Remove fade effect from landscape widget
        self.landscape_widget.setGraphicsEffect(None)
        
        # Clear any existing opacity effects on portrait slots
        for slot in self.image_slots:
            slot.setGraphicsEffect(None)
        
        # Create fade-in animation for portrait slots with staggered timing
        self.portrait_fade_effects = []
        self.portrait_fade_animations = QSequentialAnimationGroup()
        
        for i, slot in enumerate(self.image_slots):
            # Create opacity effect
            fade_effect = QGraphicsOpacityEffect()
            fade_effect.setOpacity(0.0)  # Start invisible
            slot.setGraphicsEffect(fade_effect)
            self.portrait_fade_effects.append(fade_effect)
            
            # Create fade-in animation
            fade_anim = QPropertyAnimation(fade_effect, b"opacity")
            fade_anim.setDuration(400)  # Shorter duration since they're sequential
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            self.portrait_fade_animations.addAnimation(fade_anim)
        
        # Connect completion to final setup
        self.portrait_fade_animations.finished.connect(self.finalize_portrait_transition)
        self.portrait_fade_animations.start()
        
    def finalize_portrait_transition(self):
        """Finalize portrait mode transition and restore timer states"""
        # Clear fade effects
        for slot in self.image_slots:
            slot.setGraphicsEffect(None)
        
        # Restore portrait timer states if available, otherwise use new random intervals
        if self.portrait_timer_states and len(self.portrait_timer_states) == len(self.timers):
            print(f"[DEBUG] Restoring portrait timer states: {[(s['index'], s['remaining'], s['was_active']) for s in self.portrait_timer_states]}")
            for state in self.portrait_timer_states:
                i = state['index']
                if i < len(self.timers) and state['was_active']:
                    # Use the saved remaining time, but ensure it's reasonable
                    remaining = max(state['remaining'], 1000)  # At least 1 second
                    self.timers[i].start(remaining)
                    print(f"[DEBUG] Restored timer {i} with {remaining}ms remaining")
                elif i < len(self.timers):
                    # Timer wasn't active, start with new random interval
                    interval = self.get_random_portrait_interval()
                    self.timers[i].start(interval)
                    print(f"[DEBUG] Started new timer {i} with {interval}ms")
            # Clear saved states
            self.portrait_timer_states = []
        else:
            # No saved states or mismatch, use new random intervals
            print("[DEBUG] No saved timer states, using new random intervals")
            for i in range(len(self.timers)):
                interval = self.get_random_portrait_interval()
                self.timers[i].start(interval)
        
        # Clear transition flag first so new landscape images can be detected
        self.transition_in_progress = False
        
        # Update the slot that triggered landscape mode
        if self.landscape_source_slot_index >= 0 and self.landscape_source_slot_index < len(self.image_slots):
            print(f"[DEBUG] Updating source slot {self.landscape_source_slot_index} that triggered landscape mode")
            # Stop its timer first
            self.timers[self.landscape_source_slot_index].stop()
            # Trigger immediate update
            self.change_single_image(self.landscape_source_slot_index)
            
        # Start cooldown
        self.mode_switch_cooldown.start(self.cooldown_duration)