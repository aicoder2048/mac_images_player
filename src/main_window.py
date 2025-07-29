from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, QMenu, QMessageBox,
                             QDialog, QLabel, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QActionGroup, QFont
from src.image_viewer import ImageViewer, DisplayMode
from src.music_player import MusicPlayer
from src.translations import tr, init_language, get_language, set_language
import os
import json
import subprocess


class MainWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        # Initialize language system
        init_language()
        
        self.config = config
        self.music_player = MusicPlayer()
        self.settings = QSettings('Reel77', 'Config')
        self.music_history = self.load_music_history()
        self.is_paused = False  # Track overall pause state
        self.music_was_playing = False  # Track if music was playing before pause
        self.favorites_menu = None  # Will be created in create_menu_bar
        self.init_ui()
        self.setup_music()
        
        # Connect to favorites changed signal
        self.image_viewer.favorites_changed.connect(self.update_favorites_menu)
        self.image_viewer.favorites_changed.connect(lambda: self.save_favorites_settings())
        
        # Load favorites from settings
        self.load_favorites()
        # Update favorites menu to show loaded favorites
        self.update_favorites_menu()
        
    def init_ui(self):
        self.setWindowTitle("Reel 77 - 柒柒画片机")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #141414;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image viewer
        self.image_viewer = ImageViewer(self.config)
        layout.addWidget(self.image_viewer)
        
        central_widget.setLayout(layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Set up keyboard shortcuts
        self.setup_shortcuts()
        
        # Start in fullscreen
        self.showFullScreen()
        
        # Start image display
        self.image_viewer.start()
        
    def create_menu_bar(self):
        """Create menu bar with controls"""
        # Clear existing menu bar
        menubar = self.menuBar()
        menubar.clear()
        
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2a2a2a;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu {
                background-color: #2a2a2a;
                color: white;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu(tr('file'))
        
        fullscreen_action = QAction(tr('toggle_fullscreen'), self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        file_menu.addAction(fullscreen_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(tr('exit'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Fill menu
        fill_menu = menubar.addMenu(tr('fill'))
        
        # Create action group for mutually exclusive selection
        self.display_mode_group = QActionGroup(self)
        self.display_mode_group.setExclusive(True)
        
        # Load saved display mode or default to BLUR_FILL
        saved_mode_value = self.settings.value('display_mode', DisplayMode.BLUR_FILL.value)
        saved_mode = DisplayMode.BLUR_FILL
        for mode in DisplayMode:
            if mode.value == saved_mode_value:
                saved_mode = mode
                break
        
        # Create actions for each display mode
        blur_fill_action = QAction(tr('blur_fill'), self)
        blur_fill_action.setCheckable(True)
        blur_fill_action.setChecked(saved_mode == DisplayMode.BLUR_FILL)
        blur_fill_action.setData(DisplayMode.BLUR_FILL)
        blur_fill_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.BLUR_FILL))
        self.display_mode_group.addAction(blur_fill_action)
        fill_menu.addAction(blur_fill_action)
        
        fit_action = QAction(tr('fit'), self)
        fit_action.setCheckable(True)
        fit_action.setChecked(saved_mode == DisplayMode.FIT)
        fit_action.setData(DisplayMode.FIT)
        fit_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.FIT))
        self.display_mode_group.addAction(fit_action)
        fill_menu.addAction(fit_action)
        
        zoom_fill_action = QAction(tr('zoom_fill'), self)
        zoom_fill_action.setCheckable(True)
        zoom_fill_action.setChecked(saved_mode == DisplayMode.ZOOM_FILL)
        zoom_fill_action.setData(DisplayMode.ZOOM_FILL)
        zoom_fill_action.triggered.connect(lambda: self.set_display_mode(DisplayMode.ZOOM_FILL))
        self.display_mode_group.addAction(zoom_fill_action)
        fill_menu.addAction(zoom_fill_action)
        
        # Apply the saved display mode
        self.image_viewer.set_display_mode(saved_mode)
        
        # Music menu
        music_menu = menubar.addMenu(tr('music'))
        
        play_pause_action = QAction(tr('play_pause'), self)
        play_pause_action.setShortcut('Space')
        play_pause_action.triggered.connect(self.toggle_display)
        music_menu.addAction(play_pause_action)
        
        # Add separator
        music_menu.addSeparator()
        
        # Add music selection submenu
        select_music_menu = QMenu(tr('select_music'), self)
        select_music_action = music_menu.addMenu(select_music_menu)
        
        # Remove the separate action that was causing the issue
        
        # Add current music as first item
        if self.config.get('music_file'):
            current_name = os.path.basename(self.config['music_file'])
            current_action = QAction(f'▶ {current_name}', self)
            current_action.setEnabled(False)
            select_music_menu.addAction(current_action)
            select_music_menu.addSeparator()
        
        # Add music history items
        if self.music_history:
            for music_path in self.music_history[:10]:  # Show last 10
                if os.path.exists(music_path):
                    music_name = os.path.basename(music_path)
                    action = QAction(music_name, self)
                    action.setData(music_path)
                    action.triggered.connect(lambda checked, path=music_path: self.change_music(path))
                    select_music_menu.addAction(action)
        else:
            no_history_action = QAction('No music history', self)
            no_history_action.setEnabled(False)
            select_music_menu.addAction(no_history_action)
        
        # Favorites menu
        self.favorites_menu = menubar.addMenu(tr('favorites'))
        self.update_favorites_menu()
        
        # Language menu
        language_menu = menubar.addMenu('Language/语言')
        
        # Create language action group
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        
        english_action = QAction(tr('english'), self)
        english_action.setCheckable(True)
        english_action.setChecked(get_language() == 'en')
        english_action.triggered.connect(lambda: self.change_language('en'))
        self.lang_group.addAction(english_action)
        language_menu.addAction(english_action)
        
        chinese_action = QAction(tr('chinese'), self)
        chinese_action.setCheckable(True)
        chinese_action.setChecked(get_language() == 'zh')
        chinese_action.triggered.connect(lambda: self.change_language('zh'))
        self.lang_group.addAction(chinese_action)
        language_menu.addAction(chinese_action)
            
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # ESC to exit fullscreen
        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self.exit_fullscreen)
        self.addAction(esc_action)
        
    def setup_music(self):
        """Set up background music"""
        music_file = self.config.get('music_file')
        if music_file:
            try:
                if self.music_player.load_music_file(music_file):
                    self.music_player.play()
                    # Set up timer to check for track end
                    self.music_timer = QTimer()
                    self.music_timer.timeout.connect(self.music_player.check_music_end)
                    self.music_timer.start(1000)  # Check every second
            except Exception as e:
                print(f"Warning: Could not initialize music player: {e}")
                # Continue without music
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
            
    def toggle_display(self):
        """Toggle entire display (images and music) play/pause"""
        if not self.is_paused:
            # Pause everything
            self.is_paused = True
            self.image_viewer.pause()
            # Remember if music was playing and pause it
            if hasattr(self, 'music_player'):
                self.music_was_playing = self.music_player.is_playing and not self.music_player.is_paused
                if self.music_was_playing:
                    self.music_player.pause()
        else:
            # Resume everything
            self.is_paused = False
            self.image_viewer.resume()
            # Only unpause music if it was playing before pause
            if hasattr(self, 'music_player') and self.music_was_playing:
                self.music_player.unpause()
            
    def closeEvent(self, event):
        """Clean up when closing"""
        self.image_viewer.stop()
        self.music_player.stop()
        event.accept()
        
    def load_music_history(self):
        """Load music history from settings"""
        history_json = self.settings.value('music_history', '[]')
        try:
            history = json.loads(history_json)
            # Filter out non-existent paths
            return [path for path in history if os.path.exists(path)]
        except:
            return []
            
    def change_music(self, music_path: str):
        """Change to a different music file"""
        if os.path.exists(music_path):
            # Stop current music
            self.music_player.stop()
            
            # Load and play new music
            if self.music_player.load_music_file(music_path):
                self.music_player.play()
                
                # Update config
                self.config['music_file'] = music_path
                
                # Don't recreate the entire menu bar - it causes duplicates
                # The current music is already playing, no need to update UI
                
    def set_display_mode(self, mode: DisplayMode):
        """Set the display mode for all image slots"""
        self.image_viewer.set_display_mode(mode)
        # Save the display mode preference
        self.settings.setValue('display_mode', mode.value)
        
    def change_language(self, lang_code):
        """Change the application language"""
        set_language(lang_code)
        # Recreate menu bar with new language
        self.create_menu_bar()
        
    @pyqtSlot(list)
    def update_favorites_menu(self, favorites=None):
        """Update the favorites menu with current favorites"""
        if not self.favorites_menu:
            return
            
        self.favorites_menu.clear()
        
        # Get current favorites if not provided
        if favorites is None:
            favorites = self.image_viewer.get_favorites()
        
        if not favorites:
            no_fav_action = QAction(tr('no_favorites'), self)
            no_fav_action.setEnabled(False)
            self.favorites_menu.addAction(no_fav_action)
        else:
            # Add each favorite image
            for i, image_path in enumerate(favorites):
                image_name = os.path.basename(image_path)
                # Create submenu for each favorite
                image_menu = QMenu(image_name, self)
                
                # Open in Finder action
                finder_action = QAction(tr('open_in_finder'), self)
                finder_action.triggered.connect(lambda checked, path=image_path: self.open_in_finder(path))
                image_menu.addAction(finder_action)
                
                # Open in Preview action
                preview_action = QAction(tr('open_in_preview'), self)
                preview_action.triggered.connect(lambda checked, path=image_path: self.open_in_preview(path))
                image_menu.addAction(preview_action)
                
                image_menu.addSeparator()
                
                # Remove from favorites action
                remove_action = QAction(tr('remove_from_favorites'), self)
                remove_action.triggered.connect(lambda checked, path=image_path: self.remove_from_favorites(path))
                image_menu.addAction(remove_action)
                
                self.favorites_menu.addMenu(image_menu)
        
        # Add remove all favorites option if there are favorites
        if favorites:
            self.favorites_menu.addSeparator()
            remove_all_action = QAction(tr('remove_all_favorites'), self)
            remove_all_action.triggered.connect(self.remove_all_favorites)
            self.favorites_menu.addAction(remove_all_action)
        
        # Add separator and dedicated slot options
        self.favorites_menu.addSeparator()
        
        # Enable/Disable dedicated slot action
        if len(favorites) > 1:
            if self.image_viewer.dedicated_slot_enabled:
                disable_action = QAction(tr('disable_dedicated_slot'), self)
                disable_action.triggered.connect(self.disable_dedicated_slot)
                self.favorites_menu.addAction(disable_action)
            else:
                enable_action = QAction(tr('enable_dedicated_slot'), self)
                enable_action.triggered.connect(self.enable_dedicated_slot)
                self.favorites_menu.addAction(enable_action)
        else:
            min_req_action = QAction(tr('dedicated_slot_min_requirement'), self)
            min_req_action.setEnabled(False)
            self.favorites_menu.addAction(min_req_action)
    
    def open_in_finder(self, file_path):
        """Open file location in Finder"""
        try:
            subprocess.run(['open', '-R', file_path])
        except Exception as e:
            print(f"Error opening in Finder: {e}")
    
    def open_in_preview(self, file_path):
        """Open file in Preview"""
        try:
            subprocess.run(['open', file_path])
        except Exception as e:
            print(f"Error opening in Preview: {e}")
    
    def remove_from_favorites(self, file_path):
        """Remove an image from favorites"""
        # Find the slot showing this image and update its state
        for i, slot in enumerate(self.image_viewer.image_slots):
            if slot.current_image_path == file_path:
                slot.set_favorited(False)
                self.image_viewer.on_favorite_toggled(i, file_path, False)
                break
        else:
            # Image not currently displayed, just remove from list
            favorites = self.image_viewer.get_favorites()
            if file_path in favorites:
                favorites.remove(file_path)
                self.image_viewer.set_favorites(favorites)
                self.image_viewer.favorites_changed.emit(favorites)
    
    def enable_dedicated_slot(self):
        """Enable the dedicated favorites slot"""
        self.image_viewer.enable_dedicated_slot(auto=False)
        self.save_favorites_settings()
    
    def disable_dedicated_slot(self):
        """Disable the dedicated favorites slot"""
        self.image_viewer.disable_dedicated_slot(auto=False)
        self.save_favorites_settings()
    
    def load_favorites(self):
        """Load favorites from settings"""
        try:
            favorites_json = self.settings.value('favorites', '[]')
            favorites = json.loads(favorites_json)
            # Filter out non-existent files
            favorites = [f for f in favorites if os.path.exists(f)]
            self.image_viewer.set_favorites(favorites)
            
            # Load dedicated slot settings
            dedicated_enabled = self.settings.value('dedicated_slot_enabled', False, type=bool)
            auto_disabled = self.settings.value('dedicated_slot_auto_disabled', False, type=bool)
            
            self.image_viewer.dedicated_slot_enabled = dedicated_enabled
            self.image_viewer.dedicated_slot_auto_disabled = auto_disabled
            
            # Apply dedicated slot styling only if enabled AND there are enough favorites
            if dedicated_enabled and len(favorites) > 1 and self.image_viewer.image_slots:
                self.image_viewer.image_slots[0].setStyleSheet("""
                    QFrame {
                        border: 3px solid #ffd700;
                        border-radius: 12px;
                        background-color: rgba(255, 215, 0, 10);
                    }
                """)
                self.image_viewer.image_slots[0].set_dedicated(True)
            elif dedicated_enabled and len(favorites) <= 1:
                # Dedicated slot was enabled but not enough favorites, disable it
                self.image_viewer.dedicated_slot_enabled = False
        except Exception as e:
            print(f"Error loading favorites: {e}")
    
    def save_favorites_settings(self):
        """Save favorites and dedicated slot settings"""
        favorites = self.image_viewer.get_favorites()
        self.settings.setValue('favorites', json.dumps(favorites))
        self.settings.setValue('dedicated_slot_enabled', self.image_viewer.dedicated_slot_enabled)
        self.settings.setValue('dedicated_slot_auto_disabled', self.image_viewer.dedicated_slot_auto_disabled)
        
    def remove_all_favorites(self):
        """Remove all favorites after confirmation"""
        # Show custom styled confirmation dialog
        dialog = StyledConfirmDialog(
            self,
            tr('remove_all_favorites'),
            tr('confirm_remove_all_favorites')
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Clear favorites list
            self.image_viewer.set_favorites([])
            self.image_viewer.favorites_changed.emit([])
            # Update all displayed images' favorite state
            for slot in self.image_viewer.image_slots:
                slot.set_favorited(False)
            # Also update landscape slot if exists
            if self.image_viewer.landscape_slot:
                self.image_viewer.landscape_slot.set_favorited(False)


class StyledConfirmDialog(QDialog):
    """A custom styled confirmation dialog"""
    def __init__(self, parent=None, title="", message=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(420, 200)
        
        # Remove window frame and make it frameless
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content frame with styling
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(30, 30, 30, 20)
        content_layout.setSpacing(25)
        
        # Icon and message layout
        message_layout = QHBoxLayout()
        message_layout.setSpacing(20)
        
        # Warning icon with circular background
        icon_container = QLabel()
        icon_container.setFixedSize(60, 60)
        icon_container.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 193, 7, 20);
                border: 2px solid rgba(255, 193, 7, 40);
                border-radius: 30px;
            }
        """)
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon text
        icon_label = QLabel("⚠")
        icon_label.setParent(icon_container)
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #ffc107;
                background-color: transparent;
                border: none;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setGeometry(0, 0, 60, 60)
        
        # Message text
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #ddd;
                font-size: 16px;
                font-weight: 500;
                background-color: transparent;
                border: none;
                padding: 10px 0;
            }
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        message_layout.addWidget(icon_container)
        message_layout.addWidget(self.message_label, 1)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        # No button (default)
        self.no_button = QPushButton("No")
        self.no_button.setFixedSize(100, 36)
        self.no_button.setStyleSheet("""
            QPushButton {
                background-color: #0084ff;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #0070dd;
            }
            QPushButton:pressed {
                background-color: #005bb5;
            }
        """)
        self.no_button.clicked.connect(self.reject)
        self.no_button.setDefault(True)
        
        # Yes button
        self.yes_button = QPushButton("Yes")
        self.yes_button.setFixedSize(100, 36)
        self.yes_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 18px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #444;
            }
        """)
        self.yes_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.no_button)
        button_layout.addWidget(self.yes_button)
        
        # Add to content layout
        content_layout.addLayout(message_layout)
        content_layout.addStretch()
        content_layout.addLayout(button_layout)
        
        # Add content frame to main layout
        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)
        
        # Add shadow effect
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def showEvent(self, event):
        """Center the dialog on parent window"""
        super().showEvent(event)
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)