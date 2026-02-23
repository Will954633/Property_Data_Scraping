"""
Logging module for property valuation data extraction system.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from config import LOG_LEVEL, LOG_FILE, LOG_DIR

def setup_logger(name="property_extractor"):
    """
    Set up and configure logger for the application.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create global logger instance
logger = setup_logger()
