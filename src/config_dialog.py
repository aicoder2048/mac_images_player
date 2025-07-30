from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QFileDialog,
                             QGroupBox, QMessageBox, QListWidget, QListWidgetItem,
                             QAbstractItemView, QButtonGroup, QRadioButton, QInputDialog)
from PyQt6.QtCore import Qt, QSettings
import os
import json
import uuid
from datetime import datetime
from .translations import tr, format_tr, init_language, get_language, set_language


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize language system
        init_language()
        
        # Initialize settings
        self.settings = QSettings('Reel77', 'Config')
        
        # Load image sets - handle migration from old history format
        self.load_and_migrate_image_sets()
        
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
        
    def load_and_migrate_image_sets(self):
        """Load image sets and migrate from old history format"""
        # Try to load new image sets format first
        image_sets_json = self.settings.value('image_sets', '[]')
        try:
            self.image_sets = json.loads(image_sets_json)
        except:
            self.image_sets = []
            
        # If no image sets exist, try to migrate from old formats
        if not self.image_sets:
            self._migrate_from_old_formats()
            
        # Set current selected set and directories
        self.current_set_index = 0
        if self.image_sets:
            self.current_set_id = self.image_sets[0]['id']
            self.images_dirs = self.image_sets[0]['dirs'].copy()
        else:
            # Create default set if none exist
            self._create_default_set()
            
        # Load music history (unchanged)  
        self.music_history = self.load_history('music_history')
    
    def _migrate_from_old_formats(self):
        """Migrate from old history formats to new image sets format"""
        migrated_sets = []
        
        # Try to load from images_dirs_history (multi-dir format)
        dirs_history_json = self.settings.value('images_dirs_history', '[]')
        try:
            images_dirs_history = json.loads(dirs_history_json)
            for i, dirs in enumerate(images_dirs_history[:5]):  # Keep last 5
                set_name = self._generate_set_name(dirs, i + 1)
                migrated_sets.append(self._create_set_object(set_name, dirs))
        except:
            pass
            
        # If still no sets, try old single-dir format  
        if not migrated_sets:
            old_history = self.load_history('images_history')
            if old_history:
                for i, dir_path in enumerate(old_history[:5]):
                    set_name = self._generate_set_name([dir_path], i + 1)
                    migrated_sets.append(self._create_set_object(set_name, [dir_path]))
                    
        self.image_sets = migrated_sets
        if migrated_sets:
            self.save_image_sets()
            
    def _create_default_set(self):
        """Create a default image set if none exist"""
        default_dirs = []
        if os.path.exists("./images"):
            default_dirs = [os.path.abspath("./images")]
        elif os.path.exists("./test_images"):
            default_dirs = [os.path.abspath("./test_images")]
            
        default_set = self._create_set_object("默认方案", default_dirs)
        self.image_sets = [default_set]
        self.current_set_index = 0
        self.current_set_id = default_set['id']
        self.images_dirs = default_dirs
        self.save_image_sets()
        
    def _create_set_object(self, name, dirs):
        """Create a new set object with proper structure"""
        return {
            'id': str(uuid.uuid4()),
            'name': name,
            'dirs': dirs,
            'created': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat()
        }
        
    def _generate_set_name(self, dirs, index):
        """Generate a meaningful name for a set based on its directories"""
        if not dirs:
            return f"方案 {index}"
        elif len(dirs) == 1:
            return os.path.basename(dirs[0])
        else:
            # Use the first directory name plus count
            first_dir = os.path.basename(dirs[0])
            return f"{first_dir} 等{len(dirs)}个"
        
    def init_ui(self):
        self.setWindowTitle(tr('config_title'))
        self.setFixedSize(650, 700)  # Slightly taller to accommodate language selection
        
        layout = QVBoxLayout()
        
        # Images directories selection
        self.images_group = QGroupBox(tr('image_directories'))
        images_layout = QVBoxLayout()
        
        # Set selection and management
        set_layout = QHBoxLayout()
        self.recent_label = QLabel("图片方案:")
        set_layout.addWidget(self.recent_label)
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.update_sets_combo()
        self.history_combo.currentIndexChanged.connect(self.on_set_selected)
        self._signals_connected = True  # Mark that signals are now connected
        set_layout.addWidget(self.history_combo, 1)
        
        # Set management buttons
        self.new_set_btn = QPushButton("新建")
        self.new_set_btn.setMaximumWidth(50)
        self.new_set_btn.clicked.connect(self.create_new_set)
        self.rename_set_btn = QPushButton("重命名")
        self.rename_set_btn.setMaximumWidth(60)
        self.rename_set_btn.clicked.connect(self.rename_current_set)
        self.delete_set_btn = QPushButton("删除")
        self.delete_set_btn.setMaximumWidth(50)
        self.delete_set_btn.clicked.connect(self.delete_current_set)
        
        set_layout.addWidget(self.new_set_btn)
        set_layout.addWidget(self.rename_set_btn)
        set_layout.addWidget(self.delete_set_btn)
        images_layout.addLayout(set_layout)
        
        # List widget for directories
        self.dirs_list = QListWidget()
        self.dirs_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.dirs_list.itemChanged.connect(self.on_item_changed)  # Handle checkbox changes
        images_layout.addWidget(self.dirs_list)
        
        # Buttons for directory management
        buttons_layout = QHBoxLayout()
        self.add_dir_btn = QPushButton(tr('add_directory'))
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_dir_btn = QPushButton(tr('remove'))
        self.remove_dir_btn.clicked.connect(self.remove_directory)
        self.clear_dirs_btn = QPushButton("清空方案")
        self.clear_dirs_btn.clicked.connect(self.clear_current_set_directories)
        
        buttons_layout.addWidget(self.add_dir_btn)
        buttons_layout.addWidget(self.remove_dir_btn)
        buttons_layout.addWidget(self.clear_dirs_btn)
        buttons_layout.addStretch()
        
        images_layout.addLayout(buttons_layout)
        self.images_group.setLayout(images_layout)
        
        # Music file selection
        self.music_group = QGroupBox(tr('background_music'))
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
            self.music_combo.addItem(tr('no_history'))
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
        self.music_browse_btn = QPushButton(tr('browse'))
        self.music_browse_btn.clicked.connect(self.browse_music_file)
        music_path_layout.addWidget(self.music_path_edit)
        music_path_layout.addWidget(self.music_browse_btn)
        
        music_layout.addWidget(self.music_combo)
        music_layout.addLayout(music_path_layout)
        self.music_group.setLayout(music_layout)
        
        # Image count and timing selection
        self.count_group = QGroupBox(tr('display_settings'))
        count_layout = QVBoxLayout()
        
        # Images per screen row
        images_row = QHBoxLayout()
        self.images_per_screen_label = QLabel(tr('images_per_screen'))
        images_row.addWidget(self.images_per_screen_label)
        self.count_combo = QComboBox()
        self.count_combo.addItems(["2", "3", "4"])
        self.count_combo.setCurrentText("3")
        self.count_combo.currentTextChanged.connect(self.on_count_changed)
        images_row.addWidget(self.count_combo)
        images_row.addStretch()
        count_layout.addLayout(images_row)
        
        # Timing options
        timing_label = QLabel(tr('image_change_timing'))
        timing_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        count_layout.addWidget(timing_label)
        
        # Portrait timing row
        portrait_row = QHBoxLayout()
        self.portrait_images_label = QLabel(tr('portrait_images'))
        portrait_row.addWidget(self.portrait_images_label)
        self.portrait_timing_combo = QComboBox()
        self.portrait_timing_combo.addItems([
            "2-4 seconds",
            "3-5 seconds", 
            "4-6 seconds",
            "5-7 seconds",
            "6-8 seconds"
        ])
        # Load saved preference or set default (3-5 seconds)
        saved_portrait_timing = self.settings.value('portrait_timing', '3-5 seconds')
        self.portrait_timing_combo.setCurrentText(saved_portrait_timing)
        self.portrait_timing_combo.currentTextChanged.connect(self.on_portrait_timing_changed)
        portrait_row.addWidget(self.portrait_timing_combo)
        portrait_row.addStretch()
        count_layout.addLayout(portrait_row)
        
        # Landscape timing row  
        landscape_row = QHBoxLayout()
        self.landscape_images_label = QLabel(tr('landscape_images'))
        landscape_row.addWidget(self.landscape_images_label)
        self.landscape_timing_combo = QComboBox()
        self.landscape_timing_combo.addItems([
            "2-4 seconds",
            "3-5 seconds",
            "4-6 seconds", 
            "5-7 seconds",
            "6-8 seconds"
        ])
        # Load saved preference or set default (2-4 seconds)
        saved_landscape_timing = self.settings.value('landscape_timing', '2-4 seconds')
        self.landscape_timing_combo.setCurrentText(saved_landscape_timing)
        self.landscape_timing_combo.currentTextChanged.connect(self.on_landscape_timing_changed)
        landscape_row.addWidget(self.landscape_timing_combo)
        landscape_row.addStretch()
        count_layout.addLayout(landscape_row)
        
        # Language selection
        lang_separator = QLabel("")
        lang_separator.setStyleSheet("margin-top: 10px;")
        count_layout.addWidget(lang_separator)
        
        lang_label = QLabel(tr('interface_language'))
        lang_label.setStyleSheet("font-weight: bold;")
        count_layout.addWidget(lang_label)
        
        lang_row = QHBoxLayout()
        self.lang_button_group = QButtonGroup()
        self.english_radio = QRadioButton(tr('english'))
        self.chinese_radio = QRadioButton(tr('chinese'))
        
        self.lang_button_group.addButton(self.english_radio, 0)
        self.lang_button_group.addButton(self.chinese_radio, 1)
        
        # Set current language
        if get_language() == 'en':
            self.english_radio.setChecked(True)
        else:
            self.chinese_radio.setChecked(True)
        
        # Connect language change
        self.lang_button_group.idClicked.connect(self.on_language_changed)
        
        lang_row.addWidget(self.english_radio)
        lang_row.addWidget(self.chinese_radio)
        lang_row.addStretch()
        count_layout.addLayout(lang_row)
        
        # Debug options
        debug_separator = QLabel("")
        debug_separator.setStyleSheet("margin-top: 15px;")
        count_layout.addWidget(debug_separator)
        
        debug_label = QLabel(tr('debug_options'))
        debug_label.setStyleSheet("font-weight: bold;")
        count_layout.addWidget(debug_label)
        
        debug_row = QHBoxLayout()
        log_level_label = QLabel(tr('log_level'))
        debug_row.addWidget(log_level_label)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem(tr('log_level_info'), 'INFO')
        self.log_level_combo.addItem(tr('log_level_debug'), 'DEBUG')
        
        # Load saved log level or default to INFO
        saved_log_level = self.settings.value('log_level', 'INFO')
        for i in range(self.log_level_combo.count()):
            if self.log_level_combo.itemData(i) == saved_log_level:
                self.log_level_combo.setCurrentIndex(i)
                break
        
        self.log_level_combo.currentTextChanged.connect(self.on_log_level_changed)
        debug_row.addWidget(self.log_level_combo)
        debug_row.addStretch()
        count_layout.addLayout(debug_row)
        
        self.count_group.setLayout(count_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.clear_history_btn = QPushButton(tr('clear_history'))
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.start_btn = QPushButton(tr('start'))
        self.start_btn.clicked.connect(self.on_start)
        self.start_btn.setEnabled(False)
        self.cancel_btn = QPushButton(tr('cancel'))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.clear_history_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # Add all to main layout
        layout.addWidget(self.images_group)
        layout.addWidget(self.music_group)
        layout.addWidget(self.count_group)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Now that all widgets are created, update the lists
        self.update_dirs_list()
        
        # Validate buttons and UI state
        self.validate_start_button()
        self.validate_set_management_buttons()
        
    def update_sets_combo(self):
        """Update the sets combo box with available image sets"""
        # Temporarily disconnect signal to prevent interference (only if already connected)
        signal_was_connected = False
        try:
            self.history_combo.currentIndexChanged.disconnect(self.on_set_selected)
            signal_was_connected = True
        except TypeError:
            # Signal wasn't connected yet, which is fine
            pass
        
        try:
            self.history_combo.clear()
            if self.image_sets:
                for set_obj in self.image_sets:
                    # Create display string with set name and directory count
                    dir_count = len(set_obj['dirs'])
                    if dir_count == 0:
                        display = f"{set_obj['name']} (空)"
                    elif dir_count == 1:
                        display = f"{set_obj['name']} (1个目录)"
                    else:
                        display = f"{set_obj['name']} ({dir_count}个目录)"
                    self.history_combo.addItem(display, set_obj['id'])
                
                # Select current set
                if hasattr(self, 'current_set_id'):
                    for i in range(self.history_combo.count()):
                        if self.history_combo.itemData(i) == self.current_set_id:
                            self.history_combo.setCurrentIndex(i)
                            break
            else:
                self.history_combo.addItem("无可用方案")
        finally:
            # Reconnect signal after update is complete (only if it was connected before)
            if signal_was_connected or hasattr(self, '_signals_connected'):
                self.history_combo.currentIndexChanged.connect(self.on_set_selected)
            
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
        if hasattr(self, 'clear_dirs_btn'):
            self.validate_set_management_buttons()
        
    def add_directory(self):
        """Add a new directory to the list"""
        dir_path = QFileDialog.getExistingDirectory(
            self, tr('select_images_directory'), 
            os.path.expanduser("~")
        )
        if dir_path and dir_path not in self.images_dirs:
            self.images_dirs.append(dir_path)
            self._sync_current_set_dirs()
            self.update_dirs_list()
            self.validate_set_management_buttons()
            
    def remove_directory(self):
        """Remove selected directory from the list"""
        current_row = self.dirs_list.currentRow()
        if current_row >= 0 and current_row < len(self.images_dirs):
            # Remove from our list
            self.images_dirs.pop(current_row)
            self._sync_current_set_dirs()
            # Update the UI
            self.update_dirs_list()
            self.validate_set_management_buttons()
            # Select the next appropriate item
            if self.images_dirs:
                # If there are still items, select the same row or the last one
                new_row = min(current_row, len(self.images_dirs) - 1)
                self.dirs_list.setCurrentRow(new_row)
            
            
    def on_set_selected(self, index):
        """Handle set selection from combo box"""
        if index >= 0 and self.history_combo.currentData():
            selected_set_id = self.history_combo.currentData()
            
            # Find the selected set and update current selection
            for i, set_obj in enumerate(self.image_sets):
                if set_obj['id'] == selected_set_id:
                    self.current_set_index = i
                    self.current_set_id = selected_set_id
                    self.images_dirs = set_obj['dirs'].copy()
                    
                    # Update last_used timestamp
                    set_obj['last_used'] = datetime.now().isoformat()
                    self.save_image_sets()
                    break
                    
            self.update_dirs_list()
            self.validate_set_management_buttons()
            
    def create_new_set(self):
        """Create a new image set"""
        name, ok = QInputDialog.getText(self, "新建方案", "请输入方案名称:", text="新方案")
        if ok and name.strip():
            new_set = self._create_set_object(name.strip(), [])
            self.image_sets.append(new_set)
            
            # Switch to the new set
            self.current_set_index = len(self.image_sets) - 1
            self.current_set_id = new_set['id']
            self.images_dirs = []
            
            self.save_image_sets()
            self.update_sets_combo()
            self.update_dirs_list()
            self.validate_set_management_buttons()
            
    def rename_current_set(self):
        """Rename the current image set"""
        if not hasattr(self, 'current_set_id') or not self.current_set_id:
            return
            
        # Find current set
        current_set = None
        for set_obj in self.image_sets:
            if set_obj['id'] == self.current_set_id:
                current_set = set_obj
                break
                
        if not current_set:
            return
            
        name, ok = QInputDialog.getText(self, "重命名方案", "请输入新的方案名称:", text=current_set['name'])
        if ok and name.strip() and name.strip() != current_set['name']:
            current_set['name'] = name.strip()
            self.save_image_sets()
            self.update_sets_combo()
            
    def delete_current_set(self):
        """Delete the current image set"""
        if not hasattr(self, 'current_set_id') or not self.current_set_id:
            return
            
        if len(self.image_sets) <= 1:
            QMessageBox.warning(self, "无法删除", "至少需要保留一个方案！")
            return
            
        # Find current set
        current_set = None
        current_index = -1
        for i, set_obj in enumerate(self.image_sets):
            if set_obj['id'] == self.current_set_id:
                current_set = set_obj
                current_index = i
                break
                
        if not current_set:
            return
            
        reply = QMessageBox.question(
            self, "删除方案", 
            f"确定要删除方案 '{current_set['name']}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove the set
            self.image_sets.pop(current_index)
            
            # Switch to the first available set
            if self.image_sets:
                self.current_set_index = 0
                self.current_set_id = self.image_sets[0]['id']
                self.images_dirs = self.image_sets[0]['dirs'].copy()
            else:
                # Create default set if none left
                self._create_default_set()
                
            self.save_image_sets()
            self.update_sets_combo()
            self.update_dirs_list()
            self.validate_set_management_buttons()
            
    def clear_current_set_directories(self):
        """Clear all directories from current set"""
        if not hasattr(self, 'current_set_id') or not self.current_set_id:
            return
            
        # Find current set
        current_set = None
        for set_obj in self.image_sets:
            if set_obj['id'] == self.current_set_id:
                current_set = set_obj
                break
                
        if not current_set:
            return
            
        reply = QMessageBox.question(
            self, "清空方案", 
            f"确定要清空方案 '{current_set['name']}' 中的所有目录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            current_set['dirs'] = []
            self.images_dirs = []
            self.save_image_sets()
            self.update_sets_combo()
            self.update_dirs_list()
            
    def validate_set_management_buttons(self):
        """Validate set management button states"""
        has_sets = len(self.image_sets) > 0
        has_multiple_sets = len(self.image_sets) > 1
        
        # Always allow new set creation
        self.new_set_btn.setEnabled(True)
        
        # Allow rename and clear if we have sets
        if hasattr(self, 'rename_set_btn'):
            self.rename_set_btn.setEnabled(has_sets)
        if hasattr(self, 'clear_dirs_btn'):
            self.clear_dirs_btn.setEnabled(has_sets and len(self.images_dirs) > 0)
            
        # Allow delete only if we have multiple sets
        if hasattr(self, 'delete_set_btn'):
            self.delete_set_btn.setEnabled(has_multiple_sets)
            
    def on_item_changed(self, item):
        """Handle checkbox state changes"""
        # Update current set with new directory selection
        self._update_current_set_dirs()
        self.validate_start_button()
        self.validate_set_management_buttons()
        
    def _update_current_set_dirs(self):
        """Update current set's directories based on UI state"""
        if hasattr(self, 'current_set_id') and self.current_set_id:
            checked_dirs = self.get_checked_directories()
            for set_obj in self.image_sets:
                if set_obj['id'] == self.current_set_id:
                    set_obj['dirs'] = checked_dirs
                    self.images_dirs = checked_dirs
                    break
            # Update combo display (but maintain selection)
            self.update_sets_combo()
            
    def _sync_current_set_dirs(self):
        """Sync current set's directories with self.images_dirs"""
        if hasattr(self, 'current_set_id') and self.current_set_id:
            for set_obj in self.image_sets:
                if set_obj['id'] == self.current_set_id:
                    set_obj['dirs'] = self.images_dirs.copy()
                    set_obj['last_used'] = datetime.now().isoformat()
                    break
            self.save_image_sets()
            # Update combo display to reflect new directory count (but maintain selection)
            self.update_sets_combo()
            
    def browse_music_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr('select_music_file'), 
            os.path.expanduser("~"),
            f"{tr('audio_files')} (*.mp3 *.wav *.ogg *.flac);;{tr('all_files')} (*.*)"
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
        
    def on_portrait_timing_changed(self, text):
        """Handle portrait timing change"""
        self.settings.setValue('portrait_timing', text)
        
    def on_landscape_timing_changed(self, text):
        """Handle landscape timing change"""
        self.settings.setValue('landscape_timing', text)
        
    def on_log_level_changed(self, text):
        """Handle log level change"""
        log_level = self.log_level_combo.currentData()
        self.settings.setValue('log_level', log_level)
        
    def on_language_changed(self, button_id):
        """Handle language change"""
        if button_id == 0:  # English
            set_language('en')
        else:  # Chinese
            set_language('zh')
        
        # Update UI immediately
        self.update_ui_language()
        
    def update_ui_language(self):
        """Update all UI elements with new language"""
        # Update window title
        self.setWindowTitle(tr('config_title'))
        
        # Update group box titles
        self.images_group.setTitle(tr('image_directories'))
        self.music_group.setTitle(tr('background_music'))
        self.count_group.setTitle(tr('display_settings'))
        
        # Update labels
        self.recent_label.setText("图片方案:")
        self.images_per_screen_label.setText(tr('images_per_screen'))
        self.portrait_images_label.setText(tr('portrait_images'))
        self.landscape_images_label.setText(tr('landscape_images'))
        
        # Update buttons
        self.add_dir_btn.setText(tr('add_directory'))
        self.remove_dir_btn.setText(tr('remove'))
        self.clear_dirs_btn.setText("清空方案")
        
        # Update set management buttons (these are Chinese-only for now)
        if hasattr(self, 'new_set_btn'):
            self.new_set_btn.setText("新建")
        if hasattr(self, 'rename_set_btn'):
            self.rename_set_btn.setText("重命名")
        if hasattr(self, 'delete_set_btn'):
            self.delete_set_btn.setText("删除")
        self.music_browse_btn.setText(tr('browse'))
        self.clear_history_btn.setText(tr('clear_history'))
        self.start_btn.setText(tr('start'))
        self.cancel_btn.setText(tr('cancel'))
        
        # Update radio buttons
        self.english_radio.setText(tr('english'))
        self.chinese_radio.setText(tr('chinese'))
        
        # Update debug options (if they exist)
        if hasattr(self, 'log_level_combo'):
            # Update combo box items
            for i in range(self.log_level_combo.count()):
                item_data = self.log_level_combo.itemData(i)
                if item_data == 'INFO':
                    self.log_level_combo.setItemText(i, tr('log_level_info'))
                elif item_data == 'DEBUG':
                    self.log_level_combo.setItemText(i, tr('log_level_debug'))
        
        # Update combo box placeholder text
        if self.music_combo.count() == 1 and self.music_combo.currentData() is None:
            self.music_combo.setItemText(0, tr('no_history'))
        
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
                self, tr('no_directories_title'),
                tr('no_directories_msg')
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
                self, tr('no_images_title'),
                tr('no_images_msg')
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
            'image_count': self.image_count,
            'portrait_timing': self.portrait_timing_combo.currentText(),
            'landscape_timing': self.landscape_timing_combo.currentText(),
            'log_level': self.log_level_combo.currentData()
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
        
    def save_image_sets(self):
        """Save image sets to settings"""
        self.settings.setValue('image_sets', json.dumps(self.image_sets))
        
    def save_dirs_history(self):
        """Save multi-directory history (deprecated - use save_image_sets)"""
        # Keep for backward compatibility, but redirect to new method
        self.save_image_sets()
        
    def save_current_dirs_to_history(self):
        """Update current set with selected directories"""
        checked_dirs = self.get_checked_directories()
        if hasattr(self, 'current_set_id') and self.current_set_id:
            # Update current set's directories
            for set_obj in self.image_sets:
                if set_obj['id'] == self.current_set_id:
                    set_obj['dirs'] = checked_dirs
                    set_obj['last_used'] = datetime.now().isoformat()
                    break
            self.save_image_sets()
        
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
            self, tr('clear_history_title'), 
            tr('clear_history_msg'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear image sets but keep default set
            self._create_default_set()
            
            # Clear music history
            self.music_history = []
            self.save_history('music_history', [])
            
            # Update combo boxes
            self.update_sets_combo()
            self.update_dirs_list()
            self.music_combo.clear()
            self.music_combo.addItem(tr('no_history'))
            
    def get_first_music_file(self, directory):
        """Get the first music file from a directory"""
        if not os.path.exists(directory):
            return ""
        supported_formats = {'.mp3', '.wav', '.ogg', '.flac'}
        for file in sorted(os.listdir(directory)):
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                return os.path.abspath(os.path.join(directory, file))
        return ""