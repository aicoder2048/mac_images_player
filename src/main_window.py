from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QMenu
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QAction, QKeySequence, QActionGroup
from src.image_viewer import ImageViewer, DisplayMode
from src.music_player import MusicPlayer
from src.translations import tr, init_language, get_language, set_language
import os
import json


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
        self.init_ui()
        self.setup_music()
        
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
        
        exit_action = QAction(tr('exit'), self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu(tr('view'))
        
        fullscreen_action = QAction(tr('toggle_fullscreen'), self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
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
        
        # Language menu
        language_menu = menubar.addMenu(tr('language') + '/语言')
        
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