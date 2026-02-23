# Last Edit: 31/01/2026, Friday, 7:41 pm (Brisbane Time)
"""
Logging configuration for Ollama property analysis system.
"""
import logging
import sys
from config import LOG_LEVEL, LOG_FILE, LOG_DIR
import os

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create logger
logger = logging.getLogger("ollama_property_analysis")
logger.setLevel(getattr(logging, LOG_LEVEL.upper()))

# Create formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

simple_formatter = logging.Formatter(
    '%(levelname)s: %(message)s'
)

# File handler (detailed)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(detailed_formatter)

# Console handler (simple)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
console_handler.setFormatter(simple_formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Prevent propagation to root logger
logger.propagate = False
