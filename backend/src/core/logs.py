"""
This module contains the logging configuration for the application.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_file="api.log", max_bytes=10 * 1024 * 1024, backup_count=5):
    """
    Sets up a robust logging configuration for the application.
    The log level is initially INFO and will be updated by config.py.
    """
    level = logging.INFO

    # Create a custom logger
    brain_logger = logging.getLogger("AITrainerBrain")
    brain_logger.setLevel(level)

    # Prevent propagation to the root logger's handlers
    brain_logger.propagate = False

    # Define a professional and readable formatter
    log_format = (
        "[%(asctime)s] [%(levelname)-8s] [%(name)s] "
        "[%(filename)s:%(lineno)d:%(funcName)s] %(message)s"
    )
    formatter = logging.Formatter(
        log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    # Use stderr for logs to keep stdout clean for potential piping
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    brain_logger.addHandler(console_handler)

    # File Handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    brain_logger.addHandler(file_handler)

    return brain_logger


# Initialize the logger for the application
logger = setup_logging()
