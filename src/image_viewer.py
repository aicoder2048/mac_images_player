from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy, QFrame, QGraphicsOpacityEffect, QGraphicsBlurEffect, QStackedLayout
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, pyqtSlot, QSize, QPropertyAnimation, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPalette, QColor, QTransform, QPainter, QFont, QPen, QBrush, QImage
from typing import List, Optional, Tuple
from enum import Enum
from collections import deque
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
from src.translations import tr
from src.logger import debug, info, warning, error


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
    favorite_toggled = pyqtSignal(int, str, bool)  # slot index, image path, is_favorited
    
    def __init__(self, slot_index: int, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.current_image_path = ""
        self.is_transitioning = False
        self.is_pinned = False
        self.is_favorited = False
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)  # Enable mouse tracking for hover
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
            QLabel:hover {
                background-color: rgba(80, 80, 80, 180);
            }
        """)
        self.pin_label.setText("📌")
        self.pin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pin_label.setFixedSize(40, 40)
        self.pin_label.hide()
        self.pin_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pin_label.setToolTip(tr('hint_click_to_unpin'))
        
        # Create custom tooltip widget
        self.tooltip_widget = QLabel(self)
        self.tooltip_widget.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 80);
                color: rgba(220, 220, 220, 200);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        self.tooltip_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tooltip_widget.hide()
        self.tooltip_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Create tooltip timer
        self.tooltip_timer = QTimer()
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self.hide_tooltip)
        
        # Create tooltip opacity effect
        self.tooltip_opacity = QGraphicsOpacityEffect()
        self.tooltip_widget.setGraphicsEffect(self.tooltip_opacity)
        
        # Create favorite icon label (overlay)
        self.favorite_label = QLabel(self)
        
        # Create dedicated slot label (overlay)
        self.dedicated_label = QLabel(self)
        self.dedicated_label.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 80);
                color: rgba(220, 220, 220, 200);
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 18px;
                font-weight: normal;
            }
        """)
        self.dedicated_label.setText(tr('favorites_slot'))
        self.dedicated_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dedicated_label.hide()
        self.favorite_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border-radius: 20px;
                padding: 8px;
                font-size: 20px;
            }
            QLabel:hover {
                background-color: rgba(255, 0, 0, 100);
            }
        """)
        self.favorite_label.setText("♡")  # Empty heart
        self.favorite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.favorite_label.setFixedSize(40, 40)
        self.favorite_label.hide()
        self.favorite_label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setLayout(layout)
        
    def show_image(self, image_path: str, pixmap: QPixmap, initial=False, fast_transition=False):
        """Display new image with optional transition"""
        if not pixmap:
            return
            
        if self.is_transitioning:
            debug(f"Image dropped during transition: {os.path.basename(image_path)}")
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
        # Position favorite label below pin label
        self.favorite_label.move(rect.width() - 50, 60)
        # Position dedicated label at bottom left
        self.dedicated_label.adjustSize()
        self.dedicated_label.move(10, rect.height() - self.dedicated_label.height() - 10)
        # Reposition tooltip if visible
        if self.tooltip_widget.isVisible():
            x = (rect.width() - self.tooltip_widget.width()) // 2
            self.tooltip_widget.move(x, 20)
        
    def sizeHint(self):
        """Provide size hint to maintain equal sizes"""
        return QSize(300, 600)  # Default size hint
        
    def enterEvent(self, event):
        """Show tooltip on mouse enter"""
        # Set text based on pin state
        if self.is_pinned:
            self.tooltip_widget.setText(tr('hint_click_to_unpin'))
        else:
            self.tooltip_widget.setText(tr('hint_click_to_pin'))
        
        # Adjust size and position
        self.tooltip_widget.adjustSize()
        x = (self.width() - self.tooltip_widget.width()) // 2
        y = 20  # Position near top
        self.tooltip_widget.move(x, y)
        
        # Show with fade in
        self.tooltip_widget.show()
        self.tooltip_fade_in = QPropertyAnimation(self.tooltip_opacity, b"opacity")
        self.tooltip_fade_in.setDuration(150)
        self.tooltip_fade_in.setStartValue(0)
        self.tooltip_fade_in.setEndValue(1)
        self.tooltip_fade_in.start()
        
        # Start auto-hide timer (3 seconds)
        self.tooltip_timer.start(3000)
        
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Hide tooltip on mouse leave"""
        self.tooltip_timer.stop()
        self.hide_tooltip()
        super().leaveEvent(event)
        
    def hide_tooltip(self):
        """Hide tooltip with fade out"""
        if not self.tooltip_widget.isVisible():
            return
        self.tooltip_fade_out = QPropertyAnimation(self.tooltip_opacity, b"opacity")
        self.tooltip_fade_out.setDuration(150)
        self.tooltip_fade_out.setStartValue(1)
        self.tooltip_fade_out.setEndValue(0)
        self.tooltip_fade_out.finished.connect(self.tooltip_widget.hide)
        self.tooltip_fade_out.start()
        
    def mousePressEvent(self, event):
        """Handle mouse clicks to toggle pin state or favorite"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on pin label (only when pinned)
            if self.pin_label.isVisible() and self.pin_label.geometry().contains(event.pos()):
                # Click on pin icon - unpin
                self.clicked.emit(self.slot_index)
            # Check if click is on favorite label
            elif self.favorite_label.isVisible() and self.favorite_label.geometry().contains(event.pos()):
                self.toggle_favorite()
            # Click on image area
            elif not self.is_pinned:
                # Only pin if not already pinned
                self.clicked.emit(self.slot_index)
            
    def set_pinned(self, pinned: bool):
        """Set the pinned state and update visual indicator"""
        self.is_pinned = pinned
        if pinned:
            self.pin_label.show()
            self.favorite_label.show()
        else:
            self.pin_label.hide()
            self.favorite_label.hide()
            # Note: We do NOT reset favorite state when unpinned
            # Favorites should persist independently of pin state
            
    def set_display_mode(self, mode: DisplayMode):
        """Set display mode for both labels"""
        self.current_label.set_display_mode(mode)
        self.next_label.set_display_mode(mode)
        
    def toggle_favorite(self):
        """Toggle the favorite state"""
        self.is_favorited = not self.is_favorited
        self.update_favorite_icon()
        self.favorite_toggled.emit(self.slot_index, self.current_image_path, self.is_favorited)
        
    def set_favorited(self, favorited: bool):
        """Set the favorite state"""
        self.is_favorited = favorited
        self.update_favorite_icon()
        
    def update_favorite_icon(self):
        """Update the favorite icon based on state"""
        if self.is_favorited:
            self.favorite_label.setText("♥")  # Filled heart
            self.favorite_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 0, 0, 150);
                    color: white;
                    border-radius: 20px;
                    padding: 8px;
                    font-size: 20px;
                    }
                QLabel:hover {
                    background-color: rgba(255, 0, 0, 200);
                }
            """)
        else:
            self.favorite_label.setText("♡")  # Empty heart
            self.favorite_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 0, 0, 150);
                    color: white;
                    border-radius: 20px;
                    padding: 8px;
                    font-size: 20px;
                    }
                QLabel:hover {
                    background-color: rgba(255, 0, 0, 100);
                }
            """)
            
    def set_dedicated(self, dedicated: bool):
        """Set whether this slot is a dedicated favorites slot"""
        if dedicated:
            self.dedicated_label.show()
        else:
            self.dedicated_label.hide()


class ImageViewer(QWidget):
    images_changed = pyqtSignal()
    favorites_changed = pyqtSignal(list)  # Emits list of favorite image paths
    
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
        
        # Favorites management
        self.favorites_list: List[str] = []
        self.dedicated_slot_enabled = False
        self.dedicated_slot_auto_disabled = False  # Track if user manually disabled
        
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
        
        # Preview mode tracking
        self.landscape_preview_pending = False  # Flag to prevent duplicate switches
        
        # Landscape播放管理系统
        self.landscape_lock = None  # 当前持锁的slot_index
        self.landscape_lock_time = None  # 锁获取时间
        self.landscape_lock_stage = None  # 锁阶段: 'preview' 或 'playing'
        self.landscape_queue = deque()  # 等待播放的landscape图片队列
        self.last_landscape_slot = None  # 上一个播放landscape的槽位
        self.landscape_lock_timeout = 15000  # 15秒超时
        self.force_release_timer = None  # 强制释放定时器
        
        # 抢占机制相关
        self.last_preemption_time = 0  # 上次抢占时间
        self.preemption_cooldown = 5000  # 抢占冷却时间5秒
        self.preview_stage_duration = 2000  # 预览阶段持续时间2秒
        
        # 超时检查定时器
        self.lock_timeout_timer = QTimer()
        self.lock_timeout_timer.timeout.connect(self.check_lock_timeout)
        self.lock_timeout_timer.start(1000)  # 每秒检查
        
        # 并发保护标志
        self._acquiring_lock = False
        
        # 待执行任务跟踪 - 用于取消delayed_landscape_switch
        self.pending_landscape_tasks = {}  # slot_index -> QTimer object
        
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
            slot.favorite_toggled.connect(self.on_favorite_toggled)  # Connect favorite signal
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
        self.landscape_slot.favorite_toggled.connect(self.on_favorite_toggled)  # Connect favorite signal
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
                background-color: rgba(60, 60, 60, 80);
                color: rgba(220, 220, 220, 200);
                font-size: 18px;
                font-weight: normal;
                padding: 8px 12px;
                border-radius: 8px;
            }
        """)
        self.pause_label.setText("⏸ " + tr('paused'))
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
        """Display initial image with landscape lock check"""
        original_image = image_path
        self.current_images[index] = image_path
        
        # 检查是否为landscape并通过锁系统
        if self.is_landscape_image(image_path):
            debug(f"Initial image {os.path.basename(image_path)} is landscape in slot {index}")
            # 收藏专栏使用优先级
            priority = (index == 0 and self.dedicated_slot_enabled)
            if self.acquire_landscape_lock(index, priority=priority):
                debug(f"Slot {index} acquired lock for initial landscape")
                # 成功获取锁，显示landscape并开始预览流程
                pixmap = self.load_image_for_display(image_path)
                if pixmap:
                    self.image_slots[index].show_image(image_path, pixmap, initial=True)
                    # 初始landscape也需要预览和切换流程
                    self.landscape_preview_pending = True
                    self._schedule_landscape_switch(index, image_path)
                    # 停止定时器，防止在预览期间改变图片
                    self.timers[index].stop()
                    # Set favorite state if applicable
                    if image_path in self.favorites_list:
                        self.image_slots[index].set_favorited(True)
                return
            else:
                debug(f"Slot {index} failed to acquire lock, selecting portrait instead")
                # 获取锁失败，重新选择portrait图片
                portrait_imgs = [img for img in self.image_files 
                               if self.is_portrait_image(img) and img != original_image]
                if portrait_imgs:
                    image_path = random.choice(portrait_imgs)
                    self.current_images[index] = image_path
                    debug(f"Slot {index} switched to portrait: {os.path.basename(image_path)}")
        
        # 显示最终图片（portrait或获得锁的landscape已经显示了）
        pixmap = self.load_image_for_display(image_path)
        if pixmap:
            self.image_slots[index].show_image(image_path, pixmap, initial=True)
            # Set favorite state if applicable
            if image_path in self.favorites_list:
                self.image_slots[index].set_favorited(True)
            
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
            self.pause_label.raise_()
                    
    def resume(self):
        """Resume all image changes"""
        if self.is_paused:
            self.is_paused = False
            # Hide pause indicator
            self.pause_label.hide()
            # Restart timers based on current mode
            if self.current_layout_mode == LayoutMode.PORTRAIT:
                for i in range(len(self.timers)):
                    # Only restart timer if slot is not pinned
                    if i < len(self.image_slots) and not self.image_slots[i].is_pinned:
                        interval = self.get_random_portrait_interval()
                        self.timers[i].start(interval)
            else:
                # In landscape mode, check if landscape slot is pinned
                if self.landscape_slot and not self.landscape_slot.is_pinned:
                    interval = self.get_random_landscape_interval()
                    self.landscape_timer.start(interval)
                
    def position_pause_label(self):
        """Position pause label in bottom-right corner"""
        if self.pause_label:
            self.pause_label.adjustSize()
            x = self.width() - self.pause_label.width() - 30
            y = self.height() - self.pause_label.height() - 30
            self.pause_label.move(x, y)
            self.pause_label.raise_()
            
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
            
        # 新的landscape管理系统
        new_image = None
        
        # 收藏专栏特殊处理
        if index == 0 and self.dedicated_slot_enabled and self.favorites_list:
            # 只从收藏中选择
            available = [img for img in self.favorites_list if img not in self.current_images]
            if not available:
                available = [img for img in self.favorites_list if img != self.current_images[index]]
            
            if available:
                new_image = random.choice(available)
                self.current_images[index] = new_image
                
                # 收藏专栏的landscape处理（独立于全局系统）
                if self.is_landscape_image(new_image):
                    # 直接尝试获取锁，收藏专栏使用优先级
                    if self.acquire_landscape_lock(0, priority=True):
                        # 成功获取锁，开始landscape预览流程
                        self.landscape_preview_pending = True
                        pixmap = self.load_image_for_display(new_image)
                        if pixmap:
                            self.image_slots[index].show_image(new_image, pixmap, initial=False)
                            self.images_changed.emit()
                        
                        self._schedule_landscape_switch(index, new_image)
                        # 停止定时器，直到landscape流程完全结束
                        self.timers[index].stop()
                        return
                    else:
                        # 获取锁失败，强制选择portrait图片
                        portrait_imgs = [img for img in available if self.is_portrait_image(img)]
                        if portrait_imgs:
                            new_image = random.choice(portrait_imgs)
                            self.current_images[index] = new_image
        else:
            # 普通槽位处理
            # 1. 优先检查队列中的landscape
            if self.landscape_queue:
                landscape_img = self.landscape_queue.popleft()
                if os.path.exists(landscape_img):
                    # 直接尝试获取锁
                    if self.acquire_landscape_lock(index):
                        new_image = landscape_img
                        self.current_images[index] = new_image
                        
                        # 开始landscape预览
                        self.landscape_preview_pending = True
                        pixmap = self.load_image_for_display(new_image)
                        if pixmap:
                            self.image_slots[index].show_image(new_image, pixmap, initial=False)
                            self.images_changed.emit()
                        
                        self._schedule_landscape_switch(index, new_image)
                        # 停止定时器，直到landscape流程完全结束
                        self.timers[index].stop()
                        return
                    else:
                        # 获取锁失败，重新放回队列
                        self.landscape_queue.appendleft(landscape_img)
            
            # 2. 随机选择新图片
            available = [img for img in self.image_files if img not in self.current_images]
            if not available:
                available = [img for img in self.image_files if img != self.current_images[index]]
            
            if available:
                new_image = random.choice(available)
                self.current_images[index] = new_image
                
                # 3. 处理新选择的landscape图片
                if self.is_landscape_image(new_image):
                    # 直接尝试获取锁
                    if self.acquire_landscape_lock(index):
                        # 成功获取锁，立即播放
                        self.landscape_preview_pending = True
                        pixmap = self.load_image_for_display(new_image)
                        if pixmap:
                            self.image_slots[index].show_image(new_image, pixmap, initial=False)
                            self.images_changed.emit()
                        
                        self._schedule_landscape_switch(index, new_image)
                        # 停止定时器，直到landscape流程完全结束
                        self.timers[index].stop()
                        return
                    else:
                        # 获取锁失败，加入队列并选择portrait
                        if len(self.landscape_queue) < 5:
                            self.landscape_queue.append(new_image)
                        
                        # 重新选择portrait图片
                        portrait_img = self.get_random_portrait_image(self.current_images)
                        if portrait_img:
                            new_image = portrait_img
                            self.current_images[index] = new_image
        
        # 显示最终选择的图片
        if new_image:
            pixmap = self.load_image_for_display(new_image)
            if pixmap:
                self.image_slots[index].show_image(new_image, pixmap, initial=False)
                # Update favorite state
                if new_image in self.favorites_list:
                    self.image_slots[index].set_favorited(True)
                else:
                    self.image_slots[index].set_favorited(False)
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
            
            # If we just pinned the image, restore its favorite state
            if slot.is_pinned and slot.current_image_path in self.favorites_list:
                slot.set_favorited(True)
            
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
                error(f"Error checking image {img_path}: {e}")
                # Assume portrait if can't determine
                self.portrait_images.append(img_path)
                
        info(f"Total images: {len(self.image_files)} ({len(self.portrait_images)} portrait, {len(self.landscape_images)} landscape)")
        info("Using true random selection from all images")
        
        # Show source directories info
        if 'images_dirs' in self.config:
            info(f"Images loaded from {len(self.config['images_dirs'])} directories:")
            for dir_path in self.config['images_dirs']:
                dir_count = len([f for f in self.image_files if f.startswith(dir_path)])
                info(f"  - {dir_path}: {dir_count} images")
        
    def on_cooldown_finished(self):
        """Called when mode switch cooldown expires"""
        # Cooldown finished, mode switches are now allowed
        pass
        
    def toggle_pin_landscape(self):
        """Toggle pin state for landscape slot"""
        if self.landscape_slot:
            self.landscape_slot.set_pinned(not self.landscape_slot.is_pinned)
            
            # If we just pinned the image, restore its favorite state
            if self.landscape_slot.is_pinned and self.landscape_slot.current_image_path in self.favorites_list:
                self.landscape_slot.set_favorited(True)
            
    def change_landscape_image(self):
        """Called when landscape timer expires - always return to portrait mode"""
        current_time = time.time()
        if self.last_landscape_change_time > 0:
            time_since_last = current_time - self.last_landscape_change_time
            debug(f"Landscape timer expired at {current_time:.2f}, {time_since_last:.2f}s since image shown")
        
        # Check if landscape image is pinned
        if self.landscape_slot.is_pinned:
            debug("Landscape image is pinned, staying in landscape mode")
            # Restart timer to check again later
            self.landscape_timer.setSingleShot(True)
            interval = self.get_random_landscape_interval()
            debug(f"Restarting timer with interval: {interval}ms")
            self.landscape_timer.start(interval)
            return
        
        # Always switch back to portrait mode after showing a landscape image
        debug("Landscape display complete, returning to portrait mode")
        self.switch_to_portrait_mode()
            
    def delayed_landscape_switch(self, image_path: str, slot_index: int):
        """Execute landscape switch after preview delay"""
        debug(f"Executing delayed landscape switch from slot {slot_index}")
        
        # 多重状态验证确保原子性
        if self.landscape_lock != slot_index:
            warning(f"Slot {slot_index} lost landscape lock during preview, aborting switch")
            return
            
        if self.landscape_lock_stage != 'preview':
            warning(f"Lock stage is {self.landscape_lock_stage}, expected 'preview', aborting switch")
            return
            
        if slot_index >= len(self.image_slots) or self.image_slots[slot_index].current_image_path != image_path:
            warning(f"Slot {slot_index} image changed during preview, aborting switch")
            self.release_landscape_lock(slot_index)
            return
            
        # 清除预览状态
        self.landscape_preview_pending = False
        
        # 验证切换条件
        if not self.transition_in_progress and self.current_layout_mode == LayoutMode.PORTRAIT:
            # 进入播放阶段，设置锁阶段为playing，防止被抢占
            self.landscape_lock_stage = 'playing'
            debug(f"Slot {slot_index} entering landscape playing stage")
            self.switch_to_landscape_mode_with_image(image_path, slot_index)
        else:
            # 条件不满足，释放锁并切换到portrait
            debug(f"Slot {slot_index} landscape switch conditions not met (transition: {self.transition_in_progress}, mode: {self.current_layout_mode})")
            self.release_landscape_lock(slot_index)
            self.force_slot_to_portrait(slot_index)
    
    def load_landscape_image(self, image_path: str) -> Optional[QPixmap]:
        """Load and scale landscape image"""
        return load_and_scale_image(image_path, (self.landscape_width, self.landscape_height), maintain_aspect=True)
    
    def is_portrait_image(self, image_path: str) -> bool:
        """Check if image is portrait (height >= width)"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return height >= width  # Portrait or square
        except Exception:
            return True  # Default to portrait if can't check
            
    def is_landscape_image(self, image_path: str) -> bool:
        """Check if image is landscape (width > height)"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return width > height
        except Exception:
            return False  # Default to portrait if can't check
            
    def get_random_portrait_image(self, exclude_current=None) -> Optional[str]:
        """Get a random portrait image, excluding current images"""
        portrait_images = [img for img in self.image_files 
                          if self.is_portrait_image(img)]
        if exclude_current:
            portrait_images = [img for img in portrait_images 
                             if img not in exclude_current]
        return random.choice(portrait_images) if portrait_images else None
        
    def acquire_landscape_lock(self, slot_index: int, priority: bool = False) -> bool:
        """获取landscape锁，支持优先级和抢占机制"""
        # 防止并发锁获取
        if self._acquiring_lock:
            debug(f"Slot {slot_index} blocked by concurrent lock acquisition")
            return False
            
        self._acquiring_lock = True
        
        try:
            # 基本条件检查
            if (self.current_layout_mode != LayoutMode.PORTRAIT or
                self.transition_in_progress or
                slot_index == self.last_landscape_slot):
                debug(f"Slot {slot_index} lock acquisition failed - basic conditions not met")
                return False
            
            # 如果没有锁被持有，直接获取
            if self.landscape_lock is None:
                self._grant_lock(slot_index)
                return True
            
            # 如果有锁被持有，检查是否可以抢占
            if priority and self._can_preempt(slot_index):
                debug(f"Slot {slot_index} (favorites) preempting slot {self.landscape_lock}")
                self._preempt_lock(slot_index)
                return True
            
            debug(f"Slot {slot_index} lock acquisition failed - lock held by slot {self.landscape_lock}")
            return False
            
        finally:
            self._acquiring_lock = False
    
    def _grant_lock(self, slot_index: int):
        """授予锁给指定槽位"""
        # 取消之前的强制释放定时器（如果存在）
        if self.force_release_timer is not None:
            self.force_release_timer.stop()
            self.force_release_timer = None
            debug(f"Cancelled previous force-release timer")
        
        self.landscape_lock = slot_index
        self.landscape_lock_time = time.time()
        self.landscape_lock_stage = 'preview'
        self.last_landscape_slot = slot_index
        
        debug(f"Slot {slot_index} successfully acquired landscape lock")
        
        # 设置超时自动释放
        self.force_release_timer = QTimer()
        self.force_release_timer.setSingleShot(True)
        self.force_release_timer.timeout.connect(lambda: self.force_release_lock(slot_index))
        self.force_release_timer.start(self.landscape_lock_timeout)
    
    def _can_preempt(self, slot_index: int) -> bool:
        """检查是否可以抢占当前锁"""
        # 只有收藏专栏可以抢占
        if not (slot_index == 0 and self.dedicated_slot_enabled):
            return False
        
        # 检查抢占冷却
        current_time = time.time() * 1000
        if current_time - self.last_preemption_time < self.preemption_cooldown:
            debug(f"Preemption blocked by cooldown")
            return False
        
        # 只能抢占普通专栏（非收藏专栏）
        if self.landscape_lock == 0:
            return False
        
        # 只能在预览阶段抢占
        if self.landscape_lock_stage != 'preview':
            debug(f"Cannot preempt - current stage: {self.landscape_lock_stage}")
            return False
        
        # 检查预览时间是否还在允许范围内
        elapsed_time = (time.time() - self.landscape_lock_time) * 1000
        if elapsed_time >= self.preview_stage_duration:
            debug(f"Cannot preempt - preview stage expired ({elapsed_time:.0f}ms)")
            return False
        
        return True
    
    def _preempt_lock(self, slot_index: int):
        """执行抢占操作"""
        preempted_slot = self.landscape_lock
        
        # 清理被抢占槽位的状态
        if preempted_slot < len(self.image_slots):
            self.force_slot_to_portrait(preempted_slot)
        
        # 更新抢占时间
        self.last_preemption_time = time.time() * 1000
        
        # 取消被抢占槽位的待执行任务
        self._cancel_pending_task(preempted_slot)
        
        # 授予锁给新槽位
        self._grant_lock(slot_index)
    
    def _schedule_landscape_switch(self, slot_index: int, image_path: str, delay_ms: int = 2000):
        """安全地调度delayed_landscape_switch任务"""
        # 先取消该槽位现有的待执行任务
        self._cancel_pending_task(slot_index)
        
        # 创建新的定时器
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._execute_delayed_landscape_switch(slot_index, image_path))
        
        # 记录任务
        self.pending_landscape_tasks[slot_index] = timer
        
        # 启动定时器
        timer.start(delay_ms)
        debug(f"Scheduled landscape switch for slot {slot_index} in {delay_ms}ms")
    
    def _cancel_pending_task(self, slot_index: int):
        """取消指定槽位的待执行任务"""
        if slot_index in self.pending_landscape_tasks:
            timer = self.pending_landscape_tasks[slot_index]
            if timer.isActive():
                timer.stop()
                debug(f"Cancelled pending landscape task for slot {slot_index}")
            del self.pending_landscape_tasks[slot_index]
    
    def _execute_delayed_landscape_switch(self, slot_index: int, image_path: str):
        """执行延迟的landscape切换"""
        # 清理任务记录
        if slot_index in self.pending_landscape_tasks:
            del self.pending_landscape_tasks[slot_index]
        
        # 执行原有的delayed_landscape_switch逻辑
        self.delayed_landscape_switch(image_path, slot_index)
        
    def release_landscape_lock(self, expected_holder=None) -> bool:
        """安全地释放landscape锁"""
        if expected_holder is not None and self.landscape_lock != expected_holder:
            warning(f"Slot {expected_holder} trying to release lock held by {self.landscape_lock}")
            return False
            
        debug(f"Releasing landscape lock from slot {self.landscape_lock}")
        
        # 取消强制释放定时器
        if self.force_release_timer is not None:
            self.force_release_timer.stop()
            self.force_release_timer = None
            debug(f"Cancelled force-release timer")
            
        self.landscape_lock = None
        self.landscape_lock_time = None
        self.landscape_lock_stage = None
        
        # 处理等待队列
        self.process_landscape_queue()
        return True
        
    def force_release_lock(self, original_holder: int):
        """强制释放超时的锁并清除landscape显示"""
        if self.landscape_lock == original_holder:
            debug(f"Force releasing timed-out lock from slot {original_holder}")
            
            # 立即清除该槽位的landscape显示
            if original_holder < len(self.image_slots):
                self.force_slot_to_portrait(original_holder)
                
                # 重要：立即重启定时器，因为没有landscape流程会完成
                if original_holder < len(self.timers) and not self.image_slots[original_holder].is_pinned:
                    interval = self.get_random_portrait_interval()
                    self.timers[original_holder].start(interval)
                    debug(f"Restarted timer for force-released slot {original_holder} with {interval}ms")
            
            # 清理定时器
            if self.force_release_timer is not None:
                self.force_release_timer = None
            
            # 释放锁和相关状态
            self.landscape_lock = None
            self.landscape_lock_time = None
            self.landscape_lock_stage = None
            self.landscape_preview_pending = False
            
    def check_lock_timeout(self):
        """检查锁是否超时"""
        if (self.landscape_lock is not None and 
            self.landscape_lock_time is not None):
            elapsed = (time.time() - self.landscape_lock_time) * 1000
            if elapsed > self.landscape_lock_timeout:
                self.force_release_lock(self.landscape_lock)
                
    def process_landscape_queue(self):
        """处理等待队列中的landscape图片"""
        if not self.landscape_queue or self.landscape_lock is not None:
            return
            
        # 找到一个合适的槽位来播放队列中的landscape
        for i in range(len(self.image_slots)):
            if (self.can_slot_use_global_queue(i) and 
                not self.image_slots[i].is_pinned):
                # 触发该槽位的更新
                QTimer.singleShot(500, lambda idx=i: self.trigger_slot_update(idx))
                break
                
    def trigger_slot_update(self, slot_index: int):
        """触发指定槽位的图片更新"""
        if slot_index < len(self.timers):
            self.timers[slot_index].stop()
            self.timers[slot_index].start(100)  # 快速触发
            
    def force_slot_to_portrait(self, slot_index: int):
        """强制槽位切换到portrait图片"""
        debug(f"Forcing slot {slot_index} to switch to portrait")
        
        # 取消该槽位的待执行landscape任务
        self._cancel_pending_task(slot_index)
        
        # 选择一个portrait图片
        portrait_img = self.get_random_portrait_image(self.current_images)
        if portrait_img:
            self.current_images[slot_index] = portrait_img
            pixmap = self.load_image_for_display(portrait_img)
            if pixmap:
                self.image_slots[slot_index].show_image(portrait_img, pixmap, initial=False)
                # 更新收藏状态
                if portrait_img in self.favorites_list:
                    self.image_slots[slot_index].set_favorited(True)
                else:
                    self.image_slots[slot_index].set_favorited(False)
                
                # 不在这里重启定时器 - 将在landscape流程完全结束后重启
                self.timers[slot_index].stop() 
                debug(f"Slot {slot_index} successfully switched to portrait: {os.path.basename(portrait_img)}, timer will restart after landscape flow completes")
            
    def can_slot_use_global_queue(self, slot_index: int) -> bool:
        """检查槽位是否可以使用全局landscape队列系统"""
        # 基本规则：不能连续在同一槽位播放
        if slot_index == self.last_landscape_slot:
            return False
            
        # 收藏专栏特殊处理
        if slot_index == 0 and self.dedicated_slot_enabled:
            # 收藏专栏不参与全局landscape队列系统
            return False
            
        return True
        
    def debug_timer_status(self):
        """Debug timer status"""
        if hasattr(self, 'landscape_timer'):
            # print(f"[DEBUG TIMER] Landscape timer active: {self.landscape_timer.isActive()}")
            # print(f"[DEBUG TIMER] Landscape timer interval: {self.landscape_timer.interval()}")
            # print(f"[DEBUG TIMER] Current layout mode: {self.current_layout_mode}")
            # print(f"[DEBUG TIMER] Is paused: {self.is_paused}")
            pass
        
        
    def switch_to_landscape_mode_with_image(self, image_path: str, source_slot_index: int = -1):
        """Switch to landscape mode and display the specified image"""
        if self.transition_in_progress or self.current_layout_mode == LayoutMode.LANDSCAPE:
            return
            
        self.transition_in_progress = True
        self.landscape_source_slot_index = source_slot_index
        self.landscape_preview_pending = False  # Clear preview flag
        
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
            
        debug(f"Saved portrait timer states: {[(s['index'], s['remaining'], s['was_active']) for s in self.portrait_timer_states]}")
        
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
        
        # Directly complete the transition without fading other slots
        # This keeps all slots visible during the 2-second preview
        self.complete_landscape_transition(image_path)
        
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
            # Set favorite state if applicable
            if image_path in self.favorites_list:
                self.landscape_slot.set_favorited(True)
            else:
                self.landscape_slot.set_favorited(False)
                
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
        
        # Ensure pause label stays on top if visible
        if self.is_paused and self.pause_label:
            self.pause_label.raise_()
        
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
            debug(f"Initial landscape image: {os.path.basename(image_path)}")
            pixmap = self.load_landscape_image(image_path)
            if pixmap:
                self.landscape_slot.show_image(image_path, pixmap, initial=True)
                self.landscape_image_count = 1
                # Set favorite state if applicable
                if image_path in self.favorites_list:
                    self.landscape_slot.set_favorited(True)
                else:
                    self.landscape_slot.set_favorited(False)
                
        # Start a single-shot timer to switch back to portrait after showing this landscape image
        try:
            self.landscape_timer.timeout.disconnect()
        except:
            pass  # No connections to disconnect
        self.landscape_timer.timeout.connect(self.change_landscape_image)
        self.landscape_timer.setSingleShot(True)  # Single shot - only fire once
        interval = self.get_random_landscape_interval()
        debug(f"Starting landscape timer with interval: {interval}ms (will switch to portrait after)")
        self.landscape_timer.start(interval)
        debug(f"Timer started successfully: {self.landscape_timer.isActive()}, single shot: {self.landscape_timer.isSingleShot()}")
        
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
        # First prepare portrait slots (make them ready but invisible)
        for slot in self.image_slots:
            slot.setGraphicsEffect(None)
            slot.setVisible(True)
        
        # Create fade out effect for landscape widget
        self.landscape_fade_effect = QGraphicsOpacityEffect()
        self.landscape_fade_effect.setOpacity(1.0)
        self.landscape_widget.setGraphicsEffect(self.landscape_fade_effect)
        
        # Create fade out animation for landscape
        self.landscape_fade_animation = QPropertyAnimation(self.landscape_fade_effect, b"opacity")
        self.landscape_fade_animation.setDuration(300)  # Faster fade
        self.landscape_fade_animation.setStartValue(1.0)
        self.landscape_fade_animation.setEndValue(0.3)  # Keep 30% visible during transition
        
        # Start portrait fade-in immediately (overlapping with landscape fade-out)
        QTimer.singleShot(100, self.start_portrait_fade_in)  # Start after 100ms
        
        # Connect animation completion to layout switch
        self.landscape_fade_animation.finished.connect(self.complete_portrait_transition)
        self.landscape_fade_animation.start()
        
    def start_portrait_fade_in(self):
        """Start fading in portrait slots while landscape is still partially visible"""
        # Create fade-in animation for portrait slots
        self.portrait_fade_effects = []
        self.portrait_fade_animations = QParallelAnimationGroup()
        
        for i, slot in enumerate(self.image_slots):
            # Create opacity effect
            fade_effect = QGraphicsOpacityEffect()
            fade_effect.setOpacity(0.0)  # Start invisible
            slot.setGraphicsEffect(fade_effect)
            self.portrait_fade_effects.append(fade_effect)
            
            # Create fade-in animation
            fade_anim = QPropertyAnimation(fade_effect, b"opacity")
            fade_anim.setDuration(400)  # Slightly longer for smooth blend
            fade_anim.setStartValue(0.0)
            fade_anim.setEndValue(1.0)
            self.portrait_fade_animations.addAnimation(fade_anim)
        
        self.portrait_fade_animations.start()
    
    def complete_portrait_transition(self):
        """Complete the transition to portrait mode"""
        # Switch layout
        self.current_layout_mode = LayoutMode.PORTRAIT
        self.stacked_layout.setCurrentWidget(self.portrait_widget)
        
        # Calculate portrait dimensions
        self.calculate_slot_dimensions()
        
        # Remove fade effect from landscape widget
        self.landscape_widget.setGraphicsEffect(None)
        
        # Connect completion to final setup if animations exist
        if hasattr(self, 'portrait_fade_animations') and self.portrait_fade_animations:
            self.portrait_fade_animations.finished.connect(self.finalize_portrait_transition)
        else:
            # Fallback if animations weren't started
            self.finalize_portrait_transition()
        
    def finalize_portrait_transition(self):
        """Finalize portrait mode transition and restore timer states"""
        # Clear fade effects
        for slot in self.image_slots:
            slot.setGraphicsEffect(None)
        
        # Ensure pause label stays on top if visible
        if self.is_paused and self.pause_label:
            self.pause_label.raise_()
        
        # Restore portrait timer states if available, otherwise use new random intervals
        if self.portrait_timer_states and len(self.portrait_timer_states) == len(self.timers):
            debug(f"Restoring portrait timer states: {[(s['index'], s['remaining'], s['was_active']) for s in self.portrait_timer_states]}")
            for state in self.portrait_timer_states:
                i = state['index']
                if i < len(self.timers) and state['was_active']:
                    # Use the saved remaining time, but ensure it's reasonable
                    remaining = max(state['remaining'], 1000)  # At least 1 second
                    self.timers[i].start(remaining)
                    debug(f"Restored timer {i} with {remaining}ms remaining")
                elif i < len(self.timers):
                    # Timer wasn't active, start with new random interval
                    interval = self.get_random_portrait_interval()
                    self.timers[i].start(interval)
                    debug(f"Started new timer {i} with {interval}ms")
            # Clear saved states
            self.portrait_timer_states = []
        else:
            # No saved states or mismatch, use new random intervals
            debug("No saved timer states, using new random intervals")
            for i in range(len(self.timers)):
                interval = self.get_random_portrait_interval()
                self.timers[i].start(interval)
        
        # Clear transition flag first so new landscape images can be detected
        self.transition_in_progress = False
        
        # Update landscape播放槽位 - 强制更换图片避免重复显示
        locked_slot = self.landscape_lock
        if (self.landscape_source_slot_index >= 0 and 
            self.landscape_source_slot_index < len(self.image_slots)):
            
            if self.landscape_source_slot_index == locked_slot:
                # 正常情况：同一槽位触发并播放了landscape
                if not self.image_slots[locked_slot].is_pinned:
                    debug(f"Updating landscape source slot {locked_slot} (same as locked slot)")
                    # 强制更换图片，避免继续显示同一张landscape
                    self.change_single_image(locked_slot)
                    # 然后重新启动定时器
                    interval = self.get_random_portrait_interval()
                    self.timers[locked_slot].start(interval)
                    debug(f"Restarted timer for updated slot {locked_slot} with {interval}ms")
                else:
                    # 如果是固定的，只启动定时器
                    interval = self.get_random_portrait_interval()
                    self.timers[locked_slot].start(interval)
                    debug(f"Restarted timer for pinned slot {locked_slot} with {interval}ms")
            else:
                # 异常情况：不同槽位（可能是抢占场景）
                debug(f"Updating different landscape source slot {self.landscape_source_slot_index} (locked slot: {locked_slot})")
                # 处理触发landscape的槽位
                self.timers[self.landscape_source_slot_index].stop()
                self.change_single_image(self.landscape_source_slot_index)
                
                # 处理持有锁的槽位
                if (locked_slot is not None and locked_slot < len(self.timers) and 
                    not self.image_slots[locked_slot].is_pinned):
                    interval = self.get_random_portrait_interval()
                    self.timers[locked_slot].start(interval)
                    debug(f"Restarted timer for locked slot {locked_slot} with {interval}ms")
        elif locked_slot is not None and locked_slot < len(self.timers):
            # 备用逻辑：如果没有记录source_slot_index，至少重启locked_slot的定时器
            if not self.image_slots[locked_slot].is_pinned:
                interval = self.get_random_portrait_interval()
                self.timers[locked_slot].start(interval)
                debug(f"Restarted timer for landscape slot {locked_slot} with {interval}ms")
                
        # 确保所有被强制切换到portrait的槽位的定时器都重新启动
        # 这是为了处理在landscape流程中被force_slot_to_portrait停止的定时器
        for i in range(len(self.timers)):
            if not self.timers[i].isActive() and not self.image_slots[i].is_pinned:
                debug(f"Found inactive timer for slot {i}, restarting")
                interval = self.get_random_portrait_interval()
                self.timers[i].start(interval)
                debug(f"Restarted inactive timer {i} with {interval}ms")
            
        # Start cooldown
        self.mode_switch_cooldown.start(self.cooldown_duration)
        
        # 释放landscape锁（最后执行，确保所有清理完成）
        if self.landscape_lock is not None:
            debug(f"Releasing landscape lock from slot {self.landscape_lock} after complete transition")
            self.release_landscape_lock(self.landscape_lock)
        
    @pyqtSlot(int, str, bool)
    def on_favorite_toggled(self, slot_index: int, image_path: str, is_favorited: bool):
        """Handle favorite toggle from image slot"""
        if is_favorited:
            if image_path not in self.favorites_list:
                self.favorites_list.append(image_path)
        else:
            if image_path in self.favorites_list:
                self.favorites_list.remove(image_path)
        
        # Auto-enable dedicated slot when favorites > 1 and not manually disabled
        if len(self.favorites_list) > 1 and not self.dedicated_slot_auto_disabled:
            if not self.dedicated_slot_enabled:
                self.enable_dedicated_slot(auto=True)
        elif self.dedicated_slot_enabled and len(self.favorites_list) <= 1:
            # Auto-disable if favorites <= 1
            self.disable_dedicated_slot(auto=True)
        
        # Emit signal for menu update
        self.favorites_changed.emit(self.favorites_list.copy())
    
    def enable_dedicated_slot(self, auto=False):
        """Enable the dedicated favorites slot"""
        if len(self.favorites_list) <= 1:
            return  # Not enough favorites
            
        self.dedicated_slot_enabled = True
        if not auto:
            self.dedicated_slot_auto_disabled = False
        
        # Apply special styling to slot 0
        if self.image_slots:
            self.image_slots[0].setStyleSheet("""
                QFrame {
                    border: 3px solid #ffd700;
                    border-radius: 12px;
                    background-color: rgba(255, 215, 0, 10);
                }
            """)
            self.image_slots[0].set_dedicated(True)
            
            # Force update of slot 0 to show a favorite
            if self.favorites_list:
                self.timers[0].stop()
                self.change_single_image(0)
    
    def disable_dedicated_slot(self, auto=False):
        """Disable the dedicated favorites slot"""
        self.dedicated_slot_enabled = False
        if not auto:
            self.dedicated_slot_auto_disabled = True
        
        # Remove special styling from slot 0
        if self.image_slots:
            self.image_slots[0].setStyleSheet("")
            self.image_slots[0].set_dedicated(False)
            
    def get_favorites(self):
        """Get the current favorites list"""
        return self.favorites_list.copy()
    
    def set_favorites(self, favorites: List[str]):
        """Set the favorites list (for loading from settings)"""
        self.favorites_list = favorites.copy()
        # Update all slots to reflect favorite state
        for slot in self.image_slots:
            if slot.current_image_path in self.favorites_list:
                slot.set_favorited(True)
        
        # Check if we should auto-enable or auto-disable dedicated slot
        if len(self.favorites_list) > 1 and not self.dedicated_slot_auto_disabled:
            if not self.dedicated_slot_enabled:
                self.enable_dedicated_slot(auto=True)
        elif self.dedicated_slot_enabled and len(self.favorites_list) <= 1:
            # Auto-disable if favorites <= 1
            self.disable_dedicated_slot(auto=True)