import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.config_dialog import ConfigDialog
from src.main_window import MainWindow
from src.translations import init_language
import os


def main():
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
        
        # Create and show main window
        main_window = MainWindow(config)
        main_window.show()
        
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
