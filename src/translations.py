"""
Translation system for Reel 77
Provides internationalization support for English and Chinese
"""

from PyQt6.QtCore import QSettings

# Translation dictionaries
TRANSLATIONS = {
    'en': {
        # Config Dialog
        'config_title': 'Reel 77 Configuration',
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
        
        # Tooltips
        'hint_click_to_pin': 'Click to pin',
        'hint_click_to_unpin': 'Click to unpin',
        
        # UI indicators
        'paused': 'PAUSED',
    },
    'zh': {
        # Config Dialog
        'config_title': 'Reel 77 设置',
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
        
        # Tooltips
        'hint_click_to_pin': '点击固定',
        'hint_click_to_unpin': '点击取消固定',
        
        # UI indicators
        'paused': '暂停',
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