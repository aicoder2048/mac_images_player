from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFileDialog,
                             QGroupBox, QMessageBox, QListWidget, QListWidgetItem,
                             QAbstractItemView)
from PyQt6.QtCore import Qt, QSettings
import os
import json


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize settings
        self.settings = QSettings('ImagePlayer', 'Config')
        
        # Load history - handle both old and new formats
        self.load_and_migrate_history()
        
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
        
    def load_and_migrate_history(self):
        """Load history and migrate from old single-dir format to multi-dir format"""
        # Try to load new format first
        dirs_history_json = self.settings.value('images_dirs_history', '[]')
        try:
            self.images_dirs_history = json.loads(dirs_history_json)
        except:
            self.images_dirs_history = []
            
        # Check for old format and migrate
        if not self.images_dirs_history:
            old_history = self.load_history('images_history')
            if old_history:
                # Convert old single directories to new format
                self.images_dirs_history = [[dir] for dir in old_history[:5]]  # Keep last 5
                self.save_dirs_history()
                
        # Set default directories
        if self.images_dirs_history and self.images_dirs_history[0]:
            self.images_dirs = self.images_dirs_history[0].copy()
        elif os.path.exists("./images"):
            self.images_dirs = [os.path.abspath("./images")]
        else:
            self.images_dirs = []
            
        # Load music history (unchanged)
        self.music_history = self.load_history('music_history')
        
    def init_ui(self):
        self.setWindowTitle("Mac Images Player Configuration")
        self.setFixedSize(650, 550)
        
        layout = QVBoxLayout()
        
        # Images directories selection
        images_group = QGroupBox("Image Directories")
        images_layout = QVBoxLayout()
        
        # History dropdown for quick selection
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Recent:"))
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.update_history_combo()
        self.history_combo.currentIndexChanged.connect(self.on_history_selected)
        history_layout.addWidget(self.history_combo, 1)
        images_layout.addLayout(history_layout)
        
        # List widget for directories
        self.dirs_list = QListWidget()
        self.dirs_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.dirs_list.itemChanged.connect(self.on_item_changed)  # Handle checkbox changes
        images_layout.addWidget(self.dirs_list)
        
        # Buttons for directory management
        buttons_layout = QHBoxLayout()
        self.add_dir_btn = QPushButton("Add Directory")
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_dir_btn = QPushButton("Remove")
        self.remove_dir_btn.clicked.connect(self.remove_directory)
        self.clear_dirs_btn = QPushButton("Clear All")
        self.clear_dirs_btn.clicked.connect(self.clear_directories)
        
        buttons_layout.addWidget(self.add_dir_btn)
        buttons_layout.addWidget(self.remove_dir_btn)
        buttons_layout.addWidget(self.clear_dirs_btn)
        buttons_layout.addStretch()
        
        images_layout.addLayout(buttons_layout)
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
        
        # Now that all widgets are created, update the lists
        self.update_dirs_list()
        
        # Validate start button if default directories exist
        self.validate_start_button()
        
    def update_history_combo(self):
        """Update the history combo box with recent directory combinations"""
        self.history_combo.clear()
        if self.images_dirs_history:
            for i, dirs in enumerate(self.images_dirs_history[:5]):  # Show last 5
                # Create a display string for the combination
                if len(dirs) == 1:
                    display = os.path.basename(dirs[0])
                else:
                    display = f"{len(dirs)} directories"
                self.history_combo.addItem(display, dirs)
        else:
            self.history_combo.addItem("No history")
            
    def update_dirs_list(self):
        """Update the list widget with current directories"""
        self.dirs_list.clear()
        for dir_path in self.images_dirs:
            item = QListWidgetItem(dir_path)
            item.setCheckState(Qt.CheckState.Checked)
            self.dirs_list.addItem(item)
        # Only validate if start button exists
        if hasattr(self, 'start_btn'):
            self.validate_start_button()
        
    def add_directory(self):
        """Add a new directory to the list"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Images Directory", 
            os.path.expanduser("~")
        )
        if dir_path and dir_path not in self.images_dirs:
            self.images_dirs.append(dir_path)
            self.update_dirs_list()
            
    def remove_directory(self):
        """Remove selected directory from the list"""
        current_row = self.dirs_list.currentRow()
        if current_row >= 0 and current_row < len(self.images_dirs):
            # Remove from our list
            self.images_dirs.pop(current_row)
            # Update the UI
            self.update_dirs_list()
            # Select the next appropriate item
            if self.images_dirs:
                # If there are still items, select the same row or the last one
                new_row = min(current_row, len(self.images_dirs) - 1)
                self.dirs_list.setCurrentRow(new_row)
            
    def clear_directories(self):
        """Clear all directories"""
        reply = QMessageBox.question(
            self, "Clear All Directories", 
            "Are you sure you want to remove all directories?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.images_dirs.clear()
            self.update_dirs_list()
            
    def on_history_selected(self, index):
        """Handle history combo selection"""
        if index >= 0 and self.history_combo.currentData():
            self.images_dirs = self.history_combo.currentData().copy()
            self.update_dirs_list()
            
    def on_item_changed(self, item):
        """Handle checkbox state changes"""
        self.validate_start_button()
            
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
        # Enable start button only if at least one directory is selected
        checked_dirs = self.get_checked_directories()
        self.start_btn.setEnabled(bool(checked_dirs))
        
    def get_checked_directories(self):
        """Get list of checked directories"""
        checked = []
        for i in range(self.dirs_list.count()):
            item = self.dirs_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.text())
        return checked
        
    def on_start(self):
        # Get checked directories
        checked_dirs = self.get_checked_directories()
        if not checked_dirs:
            QMessageBox.warning(
                self, "No Directories Selected",
                "Please select at least one directory."
            )
            return
            
        # Validate that at least one directory contains images
        has_any_images = False
        for directory in checked_dirs:
            if self.has_images(directory):
                has_any_images = True
                break
                
        if not has_any_images:
            QMessageBox.warning(
                self, "No Images Found",
                "None of the selected directories contain any supported image files."
            )
            return
            
        # Save the current combination to history
        self.save_current_dirs_to_history()
        
        self.accept()
        
    def has_images(self, directory):
        """Check if directory contains supported image files"""
        if not os.path.exists(directory):
            return False
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        try:
            for file in os.listdir(directory):
                if any(file.lower().endswith(fmt) for fmt in supported_formats):
                    return True
        except:
            return False
        return False
        
    def get_config(self):
        """Return configuration dictionary"""
        return {
            'images_dirs': self.get_checked_directories(),  # Changed to multiple dirs
            'music_file': self.music_file,
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
        
    def save_dirs_history(self):
        """Save multi-directory history"""
        self.settings.setValue('images_dirs_history', json.dumps(self.images_dirs_history))
        
    def save_current_dirs_to_history(self):
        """Save current directory combination to history"""
        checked_dirs = self.get_checked_directories()
        if checked_dirs:
            # Remove if already exists
            if checked_dirs in self.images_dirs_history:
                self.images_dirs_history.remove(checked_dirs)
            # Add to front
            self.images_dirs_history.insert(0, checked_dirs)
            # Keep only last 10
            self.images_dirs_history = self.images_dirs_history[:10]
            self.save_dirs_history()
        
    def add_to_history(self, path, history_list, history_key):
        """Add path to history if not already present"""
        if path and os.path.exists(path) and path not in history_list:
            history_list.insert(0, path)
            # Keep only last 10 entries
            history_list = history_list[:10]
            self.save_history(history_key, history_list)
            return history_list
        return history_list
        
            
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