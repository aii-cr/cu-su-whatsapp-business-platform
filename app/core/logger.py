"""
This file configures logging for the WhatsApp API backend.
It sets up a logger that logs to both console and a file for debugging and auditing.
"""

import logging
import os

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """
    Function to set up a logger with a file handler and a console handler.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent log propagation to the root logger
    logger.propagate = False

    return logger

# Define paths for log files
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the logs directory exists

log_file = os.path.join(LOG_DIR, "whatsapp.log")

# Ensure log file exists
if not os.path.exists(log_file):
    open(log_file, "w").close()

# Set up the logger
logger = setup_logger("whatsapp_logger", log_file)
