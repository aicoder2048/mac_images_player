"""
Translation system for Reel 77
Provides internationalization support for English and Chinese
"""

from PyQt6.QtCore import QSettings

# Translation dictionaries
TRANSLATIONS = {
    'en': {
        # Config Dialog
        'config_title': 'Reel 77 Startup Configuration',
        'image_directories': 'Image Directories',
        'recent': 'Recent:',
        'add_directory': 'Add Directory',
        'remove': 'Remove',
        'clear_all': 'Clear All',
        'background_music': 'Background Music (Optional)',
        'no_history': 'No history',
        'browse': 'Browse...',
        'display_settings': 'Display Settings',
        'images_per_screen': 'Images per screen:',
        'image_change_timing': 'Image Change Timing:',
        'portrait_images': 'Portrait (tall) images:',
        'landscape_images': 'Landscape (wide) images:',
        'clear_history': 'Clear History',
        'start': 'Start',
        'cancel': 'Cancel',
        'directories_count': '{} directories',
        
        # Time strings
        '2-4 seconds': '2-4 seconds',
        '3-5 seconds': '3-5 seconds',
        '4-6 seconds': '4-6 seconds',
        '5-7 seconds': '5-7 seconds',
        '6-8 seconds': '6-8 seconds',
        
        # Main Window Menus
        'file': 'File',
        'exit': 'Exit',
        'view': 'View',
        'toggle_fullscreen': 'Toggle Fullscreen',
        'fill': 'Fill',
        'blur_fill': 'Blur Fill',
        'fit': 'Fit',
        'zoom_fill': 'Zoom Fill',
        'music': 'Music',
        'play_pause': 'Play/Pause',
        'select_music': 'Select Music',
        'language': 'Language',
        'english': 'English',
        'chinese': '中文',
        
        # Dialog messages
        'clear_all_directories_title': 'Clear All Directories',
        'clear_all_directories_msg': 'Are you sure you want to remove all directories?',
        'no_directories_title': 'No Directories Selected',
        'no_directories_msg': 'Please select at least one directory.',
        'no_images_title': 'No Images Found',
        'no_images_msg': 'None of the selected directories contain any supported image files.',
        'clear_history_title': 'Clear History',
        'clear_history_msg': 'Are you sure you want to clear all directory history?',
        'select_images_directory': 'Select Images Directory',
        'select_music_file': 'Select Music File',
        'audio_files': 'Audio Files',
        'all_files': 'All Files',
        
        # Language selection
        'language_settings': 'Language Settings',
        'interface_language': 'Interface Language:',
        
        # Debug/Logging options
        'debug_options': 'Debug Options',
        'log_level': 'Log Level:',
        'log_level_info': 'Info',
        'log_level_debug': 'Debug',
        
        # Image Sets Management
        'image_sets': 'Image Sets:',
        'new_set': 'New',
        'rename_set': 'Rename', 
        'delete_set': 'Delete',
        'clear_set': 'Clear Set',
        'interface_language_label': 'Interface Language:',
        
        # Directory counts
        'directory_count_single': '1 directory',
        'directory_count_multiple': '{} directories',
        'empty_set': 'Empty set',
        
        # Labels that need translation updates
        'image_change_timing_label': 'Image Change Timing:',
        'interface_language_colon': 'Interface Language:',
        'debug_options_label': 'Debug Options',
        'log_level_colon': 'Log Level:',
        
        # Tooltips
        'hint_click_to_pin': 'Click to pin',
        'hint_click_to_unpin': 'Click to unpin',
        
        # UI indicators
        'paused': 'PAUSED',
        
        # Favorites feature
        'favorites': 'Favorites',
        'hint_click_to_favorite': 'Click to favorite',
        'hint_click_to_unfavorite': 'Click to unfavorite',
        'hint_click_to_unpin': 'Click to unpin',
        'open_in_finder': 'Show in Finder',
        'open_in_preview': 'Open in Preview',
        'remove_from_favorites': 'Remove from favorites',
        'enable_dedicated_slot': 'Enable dedicated favorites slot',
        'disable_dedicated_slot': 'Disable dedicated favorites slot',
        'favorites_slot': 'Favorites Column',
        'no_favorites': 'No favorites yet',
        'dedicated_slot_min_requirement': 'Need at least 2 favorites to enable dedicated slot',
        'remove_all_favorites': 'Remove all favorites',
        'confirm_remove_all_favorites': 'Are you sure you want to remove all favorites?',
    },
    'zh': {
        # Config Dialog
        'config_title': '柒柒(Reel77)画片机启动设置',
        'image_directories': '图片目录',
        'recent': '最近使用:',
        'add_directory': '添加目录',
        'remove': '移除',
        'clear_all': '清除全部',
        'background_music': '背景音乐 (可选)',
        'no_history': '无历史记录',
        'browse': '浏览...',
        'display_settings': '显示设置',
        'images_per_screen': '每屏图片数:',
        'image_change_timing': '图片切换时间:',
        'portrait_images': '竖屏 (纵向) 图片:',
        'landscape_images': '横屏 (横向) 图片:',
        'clear_history': '清除历史',
        'start': '开始',
        'cancel': '取消',
        'directories_count': '{} 个目录',
        
        # Time strings
        '2-4 seconds': '2-4 秒',
        '3-5 seconds': '3-5 秒',
        '4-6 seconds': '4-6 秒',
        '5-7 seconds': '5-7 秒',
        '6-8 seconds': '6-8 秒',
        
        # Main Window Menus
        'file': '文件',
        'exit': '退出',
        'view': '视图',
        'toggle_fullscreen': '切换全屏',
        'fill': '填充',
        'blur_fill': '模糊填充',
        'fit': '适应',
        'zoom_fill': '缩放填充',
        'music': '音乐',
        'play_pause': '播放/暂停',
        'select_music': '选择音乐',
        'language': '语言',
        'english': 'English',
        'chinese': '中文',
        
        # Dialog messages
        'clear_all_directories_title': '清除所有目录',
        'clear_all_directories_msg': '您确定要移除所有目录吗？',
        'no_directories_title': '未选择目录',
        'no_directories_msg': '请至少选择一个目录。',
        'no_images_title': '未找到图片',
        'no_images_msg': '所选目录中没有找到支持的图片文件。',
        'clear_history_title': '清除历史',
        'clear_history_msg': '您确定要清除所有目录历史记录吗？',
        'select_images_directory': '选择图片目录',
        'select_music_file': '选择音乐文件',
        'audio_files': '音频文件',
        'all_files': '所有文件',
        
        # Language selection
        'language_settings': '语言设置',
        'interface_language': '界面语言:',
        
        # Debug/Logging options
        'debug_options': '调试选项',
        'log_level': '日志级别:',
        'log_level_info': '信息',
        'log_level_debug': '调试',
        
        # Image Sets Management
        'image_sets': '图片方案:',
        'new_set': '新建',
        'rename_set': '重命名', 
        'delete_set': '删除',
        'clear_set': '清空方案',
        'interface_language_label': '界面语言:',
        
        # Directory counts
        'directory_count_single': '1个目录',
        'directory_count_multiple': '{}个目录',
        'empty_set': '空方案',
        
        # Labels that need translation updates
        'image_change_timing_label': '图片切换时间:',
        'interface_language_colon': '界面语言:',
        'debug_options_label': '调试选项',
        'log_level_colon': '日志级别:',
        
        # Tooltips
        'hint_click_to_pin': '点击固定',
        'hint_click_to_unpin': '点击取消固定',
        
        # UI indicators
        'paused': '暂停',
        
        # Favorites feature
        'favorites': '收藏',
        'hint_click_to_favorite': '点击收藏',
        'hint_click_to_unfavorite': '点击取消收藏',
        'hint_click_to_unpin': '点击取消固定',
        'open_in_finder': '在Finder中显示',
        'open_in_preview': '在预览中打开',
        'remove_from_favorites': '移除收藏',
        'enable_dedicated_slot': '启用收藏专属播放槽',
        'disable_dedicated_slot': '禁用收藏专属播放槽',
        'favorites_slot': '收藏专栏',
        'no_favorites': '暂无收藏',
        'dedicated_slot_min_requirement': '需要至少2个收藏才能启用专属播放槽',
        'remove_all_favorites': '移除所有收藏',
        'confirm_remove_all_favorites': '您确定要移除所有收藏吗？',
    }
}

# Global language setting
_current_language = 'en'  # Default to English

def init_language():
    """Initialize language from settings"""
    global _current_language
    settings = QSettings('Reel77', 'Config')
    _current_language = settings.value('language', 'en')

def get_language():
    """Get current language code"""
    return _current_language

def set_language(lang_code):
    """Set current language and save to settings"""
    global _current_language
    if lang_code in TRANSLATIONS:
        _current_language = lang_code
        settings = QSettings('Reel77', 'Config')
        settings.setValue('language', lang_code)

def tr(key):
    """Translate a key to current language"""
    return TRANSLATIONS.get(_current_language, {}).get(key, key)

def format_tr(key, *args, **kwargs):
    """Translate and format a string"""
    translated = tr(key)
    if args:
        return translated.format(*args)
    elif kwargs:
        return translated.format(**kwargs)
    return translated