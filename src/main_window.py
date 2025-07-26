from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence
from src.image_viewer import ImageViewer
from src.music_player import MusicPlayer


class MainWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.music_player = MusicPlayer()
        self.init_ui()
        self.setup_music()
        
    def init_ui(self):
        self.setWindowTitle("Image Player")
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
        menubar = self.menuBar()
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
        file_menu = menubar.addMenu('File')
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        fullscreen_action = QAction('Toggle Fullscreen', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Music menu
        if self.config.get('music_dir'):
            music_menu = menubar.addMenu('Music')
            
            play_pause_action = QAction('Play/Pause', self)
            play_pause_action.setShortcut('Space')
            play_pause_action.triggered.connect(self.toggle_music)
            music_menu.addAction(play_pause_action)
            
            next_track_action = QAction('Next Track', self)
            next_track_action.setShortcut('N')
            next_track_action.triggered.connect(self.music_player.next_track)
            music_menu.addAction(next_track_action)
            
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        # ESC to exit fullscreen
        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self.exit_fullscreen)
        self.addAction(esc_action)
        
    def setup_music(self):
        """Set up background music"""
        music_dir = self.config.get('music_dir')
        if music_dir:
            try:
                if self.music_player.load_music_directory(music_dir):
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
            
    def toggle_music(self):
        """Toggle music play/pause"""
        if hasattr(self, 'music_timer') and self.music_player.is_playing:
            if pygame.mixer.music.get_busy():
                self.music_player.pause()
            else:
                self.music_player.unpause()
            
    def closeEvent(self, event):
        """Clean up when closing"""
        self.image_viewer.stop()
        self.music_player.stop()
        event.accept()