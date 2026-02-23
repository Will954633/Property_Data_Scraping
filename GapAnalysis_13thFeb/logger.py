"""
Logging configuration for GPT enrichment pipeline.
Last Edit: 13/02/2026, 3:26 PM (Thursday) — Brisbane Time

Description: Centralized logging setup with file and console handlers,
progress tracking, and error logging for the enrichment pipeline.

Edit History:
- 13/02/2026 3:26 PM: Initial creation for production pipeline
"""

import logging
import sys
from pathlib import Path
from config import (
    LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT,
    MAIN_LOG_FILE, ERROR_LOG_FILE, PROGRESS_LOG_FILE, LOG_DIR
)

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# MAIN LOGGER
# ============================================================================

# Create main logger
logger = logging.getLogger("enrichment_pipeline")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create formatters
detailed_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
simple_formatter = logging.Formatter('%(levelname)s - %(message)s')

# Main file handler (all logs)
main_file_handler = logging.FileHandler(MAIN_LOG_FILE)
main_file_handler.setLevel(logging.DEBUG)
main_file_handler.setFormatter(detailed_formatter)

# Error file handler (errors only)
error_file_handler = logging.FileHandler(ERROR_LOG_FILE)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(detailed_formatter)

# Console handler (simple format)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, LOG_LEVEL))
console_handler.setFormatter(simple_formatter)

# Add handlers to main logger
logger.addHandler(main_file_handler)
logger.addHandler(error_file_handler)
logger.addHandler(console_handler)

# Prevent propagation to root logger
logger.propagate = False

# ============================================================================
# PROGRESS LOGGER (separate for monitoring)
# ============================================================================

progress_logger = logging.getLogger("enrichment_progress")
progress_logger.setLevel(logging.INFO)

# Progress file handler
progress_file_handler = logging.FileHandler(PROGRESS_LOG_FILE)
progress_file_handler.setLevel(logging.INFO)
progress_file_handler.setFormatter(detailed_formatter)

progress_logger.addHandler(progress_file_handler)
progress_logger.propagate = False

# ============================================================================
# WORKER LOGGERS (for parallel processing)
# ============================================================================

def get_worker_logger(worker_id: int) -> logging.Logger:
    """
    Create a dedicated logger for a specific worker.
    
    Args:
        worker_id: Worker identifier (1-10)
    
    Returns:
        Configured logger for the worker
    """
    worker_logger = logging.getLogger(f"worker_{worker_id}")
    worker_logger.setLevel(logging.DEBUG)
    
    # Worker-specific log file
    worker_log_file = LOG_DIR / f"worker_{worker_id}.log"
    worker_file_handler = logging.FileHandler(worker_log_file)
    worker_file_handler.setLevel(logging.DEBUG)
    worker_file_handler.setFormatter(detailed_formatter)
    
    worker_logger.addHandler(worker_file_handler)
    worker_logger.propagate = False
    
    return worker_logger

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_enrichment_start(address: str, worker_id: int = None):
    """Log the start of property enrichment."""
    msg = f"Starting enrichment for: {address}"
    if worker_id:
        msg += f" (Worker {worker_id})"
    logger.info(msg)
    progress_logger.info(msg)


def log_enrichment_success(address: str, duration: float, worker_id: int = None):
    """Log successful property enrichment."""
    msg = f"✅ Enriched: {address} ({duration:.1f}s)"
    if worker_id:
        msg += f" (Worker {worker_id})"
    logger.info(msg)
    progress_logger.info(msg)


def log_enrichment_failure(address: str, error: str, worker_id: int = None):
    """Log failed property enrichment."""
    msg = f"❌ Failed: {address} - {error}"
    if worker_id:
        msg += f" (Worker {worker_id})"
    logger.error(msg)
    progress_logger.error(msg)


def log_progress(completed: int, total: int, worker_id: int = None):
    """Log overall progress."""
    percentage = (completed / total * 100) if total > 0 else 0
    msg = f"Progress: {completed}/{total} ({percentage:.1f}%)"
    if worker_id:
        msg += f" (Worker {worker_id})"
    progress_logger.info(msg)


# Aliases for compatibility
log_enrichment_error = log_enrichment_failure


# ============================================================================
# INITIALIZATION MESSAGE
# ============================================================================

logger.info("=" * 80)
logger.info("GPT ENRICHMENT PIPELINE - LOGGING INITIALIZED")
logger.info("=" * 80)
logger.info(f"Main log: {MAIN_LOG_FILE}")
logger.info(f"Error log: {ERROR_LOG_FILE}")
logger.info(f"Progress log: {PROGRESS_LOG_FILE}")
logger.info(f"Log level: {LOG_LEVEL}")
logger.info("=" * 80)
