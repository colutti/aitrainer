"""
This module contains the logging configuration for the application.
"""
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(log_file='api.log', max_bytes=10*1024*1024, backup_count=5, level=logging.INFO):
    """
    Sets up a robust logging configuration for the application,
    outputting to both console and a rotating file.

    Args:
        log_file (str): The name of the log file.
        max_bytes (int): The maximum size of the log file before rotation (in bytes).
        backup_count (int): The number of backup log files to keep.
        level (int): The minimum logging level to capture (e.g., logging.INFO, logging.DEBUG).
    """
    # Create a custom logger
    logger = logging.getLogger("AITrainerBrain")
    logger.setLevel(level)

    # Prevent propagation to the root logger's handlers
    logger.propagate = False

    # Define a professional and readable formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] [%(filename)s:%(lineno)d:%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Initialize the logger for the application
logger = setup_logging()