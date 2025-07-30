import sys
import os
from PyQt6.QtWidgets import QApplication

# Suppress Qt warnings including QPainter warnings
os.environ['QT_LOGGING_RULES'] = '*=false'
os.environ['QT_LOGGING_CATEGORY'] = 'false'
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
from src.config_dialog import ConfigDialog
from src.main_window import MainWindow
from src.translations import init_language
from src.logger import set_log_level, info


def qt_message_handler(mode, context, message):
    """Suppress Qt warnings"""
    # Filter out QPainter warnings
    if 'QPainter' in message:
        return
    # You can add other message filters here if needed
    pass


def main():
    # Install custom message handler to suppress Qt warnings
    qInstallMessageHandler(qt_message_handler)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Reel 77")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'Reel77.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Initialize language system
    init_language()
    
    # Show configuration dialog
    config_dialog = ConfigDialog()
    if config_dialog.exec() == ConfigDialog.DialogCode.Accepted:
        config = config_dialog.get_config()
        
        # Initialize logger with selected level
        log_level = config.get('log_level', 'INFO')
        set_log_level(log_level)
        info(f"Reel 77 starting with log level: {log_level}")
        
        # Create and show main window
        main_window = MainWindow(config)
        main_window.show()
        
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
