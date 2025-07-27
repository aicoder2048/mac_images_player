import sys
from PyQt6.QtWidgets import QApplication
from src.config_dialog import ConfigDialog
from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Reel 77")
    
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
