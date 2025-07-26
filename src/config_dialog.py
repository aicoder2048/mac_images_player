from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFileDialog,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
import os


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set default directories
        self.images_dir = os.path.abspath("./images") if os.path.exists("./images") else ""
        self.music_dir = os.path.abspath("./music") if os.path.exists("./music") else ""
        self.image_count = 3
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Image Player Configuration")
        self.setFixedSize(500, 350)
        
        layout = QVBoxLayout()
        
        # Images directory selection
        images_group = QGroupBox("Images Directory")
        images_layout = QHBoxLayout()
        self.images_path_edit = QLineEdit()
        self.images_path_edit.setReadOnly(True)
        self.images_path_edit.setText(self.images_dir)
        self.images_browse_btn = QPushButton("Browse...")
        self.images_browse_btn.clicked.connect(self.browse_images_dir)
        images_layout.addWidget(self.images_path_edit)
        images_layout.addWidget(self.images_browse_btn)
        images_group.setLayout(images_layout)
        
        # Music directory selection
        music_group = QGroupBox("Music Directory (Optional)")
        music_layout = QHBoxLayout()
        self.music_path_edit = QLineEdit()
        self.music_path_edit.setReadOnly(True)
        self.music_path_edit.setText(self.music_dir)
        self.music_browse_btn = QPushButton("Browse...")
        self.music_browse_btn.clicked.connect(self.browse_music_dir)
        music_layout.addWidget(self.music_path_edit)
        music_layout.addWidget(self.music_browse_btn)
        music_group.setLayout(music_layout)
        
        # Image count selection
        count_group = QGroupBox("Display Settings")
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Images per screen:"))
        self.count_combo = QComboBox()
        self.count_combo.addItems(["2", "3", "4"])
        self.count_combo.setCurrentText("3")
        self.count_combo.currentTextChanged.connect(self.on_count_changed)
        count_layout.addWidget(self.count_combo)
        count_layout.addStretch()
        count_group.setLayout(count_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # Add all to main layout
        layout.addWidget(images_group)
        layout.addWidget(music_group)
        layout.addWidget(count_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Validate start button if default directories exist
        self.validate_start_button()
        
    def browse_images_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Images Directory", 
            os.path.expanduser("~")
        )
        if dir_path:
            self.images_dir = dir_path
            self.images_path_edit.setText(dir_path)
            self.validate_start_button()
            
    def browse_music_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Music Directory", 
            os.path.expanduser("~")
        )
        if dir_path:
            self.music_dir = dir_path
            self.music_path_edit.setText(dir_path)
            
    def on_count_changed(self, text):
        self.image_count = int(text)
        
    def validate_start_button(self):
        # Enable start button only if images directory is selected
        self.start_btn.setEnabled(bool(self.images_dir))
        
    def on_start(self):
        # Validate that images directory contains images
        if not self.has_images(self.images_dir):
            QMessageBox.warning(
                self, "No Images Found",
                "The selected directory does not contain any supported image files."
            )
            return
            
        self.accept()
        
    def has_images(self, directory):
        """Check if directory contains supported image files"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        for file in os.listdir(directory):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                return True
        return False
        
    def get_config(self):
        """Return configuration dictionary"""
        return {
            'images_dir': self.images_dir,
            'music_dir': self.music_dir,
            'image_count': self.image_count
        }