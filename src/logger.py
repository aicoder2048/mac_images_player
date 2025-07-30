"""
Professional logging system for Reel 77
Provides configurable logging with colored console output and proper formatting
"""

import logging
import sys
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration for configuration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # ANSI color codes
    COLORS = {
        logging.DEBUG: '\033[36m',    # Cyan
        logging.INFO: '\033[32m',     # Green
        logging.WARNING: '\033[33m',  # Yellow
        logging.ERROR: '\033[31m',    # Red
        logging.CRITICAL: '\033[35m'  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Get the original formatted message
        formatted = super().format(record)
        
        # Add color if this is a console handler
        if hasattr(self, '_use_colors') and self._use_colors:
            color = self.COLORS.get(record.levelno, '')
            if color:
                formatted = f"{color}{formatted}{self.RESET}"
        
        return formatted


class Logger:
    """Centralized logger for Reel 77 application"""
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup the logger with appropriate handlers and formatters"""
        self._logger = logging.getLogger('Reel77')
        self._logger.setLevel(logging.DEBUG)  # Always capture all levels
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter with timestamp, module, level, and message
        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)8s] %(name)s.%(module)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Enable colors for console output
        formatter._use_colors = True
        console_handler.setFormatter(formatter)
        
        # Set default level to INFO
        console_handler.setLevel(logging.INFO)
        
        self._logger.addHandler(console_handler)
        self._console_handler = console_handler
    
    def set_level(self, level: str):
        """Set the logging level"""
        if self._console_handler:
            log_level = getattr(logging, level.upper(), logging.INFO)
            self._console_handler.setLevel(log_level)
            self.info(f"Log level set to {level.upper()}")
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        if self._logger:
            self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        if self._logger:
            self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        if self._logger:
            self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        if self._logger:
            self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        if self._logger:
            self._logger.critical(message, *args, **kwargs)


# Global logger instance
logger = Logger()


def get_logger() -> Logger:
    """Get the global logger instance"""
    return logger


def set_log_level(level: str):
    """Set the global log level"""
    logger.set_level(level)


def debug(message: str, *args, **kwargs):
    """Convenience function for debug logging"""
    logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Convenience function for info logging"""
    logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Convenience function for warning logging"""
    logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Convenience function for error logging"""
    logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Convenience function for critical logging"""
    logger.critical(message, *args, **kwargs)