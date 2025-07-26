from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFileDialog,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QSettings
import os
import json


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize settings
        self.settings = QSettings('ImagePlayer', 'Config')
        
        # Load history
        self.images_history = self.load_history('images_history')
        self.music_history = self.load_history('music_history')
        
        # Set default directories
        # Use top of history if available, else fall back to ./images
        if self.images_history:
            self.images_dir = self.images_history[0]
        elif os.path.exists("./images"):
            self.images_dir = os.path.abspath("./images")
        else:
            self.images_dir = ""
            
        # Set default music file
        # Use top of history if available, else find first mp3 in ./music
        if self.music_history:
            self.music_file = self.music_history[0]
        elif os.path.exists("./music"):
            self.music_file = self.get_first_music_file("./music")
        else:
            self.music_file = ""
            
        self.image_count = 3
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Image Player Configuration")
        self.setFixedSize(550, 450)
        
        layout = QVBoxLayout()
        
        # Images directory selection
        images_group = QGroupBox("Images Directory")
        images_layout = QVBoxLayout()
        
        # Dropdown for history
        self.images_combo = QComboBox()
        self.images_combo.setEditable(False)
        if self.images_history:
            self.images_combo.addItems(self.images_history)
            self.images_combo.setCurrentIndex(0)  # Select first item (most recent)
        else:
            self.images_combo.addItem("No history")
            if self.images_dir:  # If we have a default ./images dir
                self.images_combo.addItem(self.images_dir)
                self.images_combo.setCurrentIndex(1)
        self.images_combo.currentTextChanged.connect(self.on_images_combo_changed)
        
        # Path display and browse button
        path_layout = QHBoxLayout()
        self.images_path_edit = QLineEdit()
        self.images_path_edit.setReadOnly(True)
        self.images_path_edit.setText(self.images_dir)
        self.images_browse_btn = QPushButton("Browse...")
        self.images_browse_btn.clicked.connect(self.browse_images_dir)
        path_layout.addWidget(self.images_path_edit)
        path_layout.addWidget(self.images_browse_btn)
        
        images_layout.addWidget(self.images_combo)
        images_layout.addLayout(path_layout)
        images_group.setLayout(images_layout)
        
        # Music file selection
        music_group = QGroupBox("Background Music (Optional)")
        music_layout = QVBoxLayout()
        
        # Dropdown for history
        self.music_combo = QComboBox()
        self.music_combo.setEditable(False)
        
        if self.music_history:
            # Show only filenames in dropdown
            for file_path in self.music_history:
                self.music_combo.addItem(os.path.basename(file_path), file_path)
            self.music_combo.setCurrentIndex(0)  # Select first item (most recent)
        else:
            self.music_combo.addItem("No history")
            # If we found a default music file, add it
            if self.music_file:
                self.music_combo.addItem(os.path.basename(self.music_file), self.music_file)
                self.music_combo.setCurrentIndex(1)
                
        self.music_combo.currentIndexChanged.connect(self.on_music_combo_changed)
        
        # Path display and browse button
        music_path_layout = QHBoxLayout()
        self.music_path_edit = QLineEdit()
        self.music_path_edit.setReadOnly(True)
        self.music_path_edit.setText(self.music_file)
        self.music_browse_btn = QPushButton("Browse...")
        self.music_browse_btn.clicked.connect(self.browse_music_file)
        music_path_layout.addWidget(self.music_path_edit)
        music_path_layout.addWidget(self.music_browse_btn)
        
        music_layout.addWidget(self.music_combo)
        music_layout.addLayout(music_path_layout)
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
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.clear_history_btn)
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
            
            # Add to history
            self.images_history = self.add_to_history(dir_path, self.images_history, 'images_history')
            
            # Update combo box
            self.images_combo.clear()
            self.images_combo.addItems(self.images_history)
            self.images_combo.setCurrentIndex(0)  # Select the newly added item
            
    def browse_music_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", 
            os.path.expanduser("~"),
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;All Files (*.*)"
        )
        if file_path:
            self.music_file = file_path
            self.music_path_edit.setText(file_path)
            
            # Add to history
            self.music_history = self.add_to_history(file_path, self.music_history, 'music_history')
            
            # Update combo box
            self.music_combo.clear()
            for path in self.music_history:
                self.music_combo.addItem(os.path.basename(path), path)
            self.music_combo.setCurrentIndex(0)  # Select the newly added item
            
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
            'music_file': self.music_file,  # Changed from music_dir
            'image_count': self.image_count
        }
        
    def load_history(self, key):
        """Load history from settings"""
        history_json = self.settings.value(key, '[]')
        try:
            history = json.loads(history_json)
            # Filter out non-existent paths
            return [path for path in history if os.path.exists(path)]
        except:
            return []
            
    def save_history(self, key, history_list):
        """Save history to settings"""
        self.settings.setValue(key, json.dumps(history_list))
        
    def add_to_history(self, path, history_list, history_key):
        """Add path to history if not already present"""
        if path and os.path.exists(path) and path not in history_list:
            history_list.insert(0, path)
            # Keep only last 10 entries
            history_list = history_list[:10]
            self.save_history(history_key, history_list)
            return history_list
        return history_list
        
    def on_images_combo_changed(self, text):
        """Handle images combo selection"""
        if text and text != "No history" and os.path.exists(text):
            self.images_dir = text
            self.images_path_edit.setText(text)
            self.validate_start_button()
            
    def on_music_combo_changed(self, index):
        """Handle music combo selection"""
        if index >= 0:
            file_path = self.music_combo.itemData(index)
            if file_path and os.path.exists(file_path):
                self.music_file = file_path
                self.music_path_edit.setText(file_path)
            
    def clear_history(self):
        """Clear all history"""
        reply = QMessageBox.question(
            self, "Clear History", 
            "Are you sure you want to clear all directory history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.images_history = []
            self.music_history = []
            self.save_history('images_history', [])
            self.save_history('music_history', [])
            
            # Update combo boxes
            self.images_combo.clear()
            self.images_combo.addItem("No history")
            self.music_combo.clear()
            self.music_combo.addItem("No history")
            
    def get_first_music_file(self, directory):
        """Get the first music file from a directory"""
        if not os.path.exists(directory):
            return ""
        supported_formats = {'.mp3', '.wav', '.ogg', '.flac'}
        for file in sorted(os.listdir(directory)):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                return os.path.abspath(os.path.join(directory, file))
        return ""