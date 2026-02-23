"""
Worker logging module with timestamped directory support.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from config import LOG_DIR, LOG_LEVEL, ENABLE_WORKER_LOGS

def setup_run_directory():
    """
    Create a timestamped run directory for logs.
    
    Returns:
        Path object for the run directory
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(LOG_DIR) / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def setup_worker_logger(worker_id, run_dir):
    """
    Set up a logger for a specific worker.
    
    Args:
        worker_id: Worker ID (integer)
        run_dir: Path to the run directory
        
    Returns:
        Logger instance configured for the worker
    """
    logger_name = f"worker_{worker_id:02d}"
    worker_logger = logging.getLogger(logger_name)
    worker_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    worker_logger.handlers = []
    
    # Create file handler
    if ENABLE_WORKER_LOGS:
        log_file = run_dir / f"worker_{worker_id:02d}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        worker_logger.addHandler(file_handler)
    
    # Also log to console (optional, can be disabled for cleaner output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_formatter = logging.Formatter(
        f'[Worker-{worker_id:02d}] %(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    worker_logger.addHandler(console_handler)
    
    return worker_logger

def setup_coordinator_logger(run_dir):
    """
    Set up a logger for the coordinator process.
    
    Args:
        run_dir: Path to the run directory
        
    Returns:
        Logger instance configured for the coordinator
    """
    coordinator_logger = logging.getLogger("coordinator")
    coordinator_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Remove existing handlers
    coordinator_logger.handlers = []
    
    # Create file handler
    log_file = run_dir / "coordinator.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    coordinator_logger.addHandler(file_handler)
    
    # Console handler for coordinator
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[COORDINATOR] %(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    coordinator_logger.addHandler(console_handler)
    
    return coordinator_logger

def setup_progress_logger(run_dir):
    """
    Set up a logger for progress tracking.
    
    Args:
        run_dir: Path to the run directory
        
    Returns:
        Logger instance configured for progress tracking
    """
    progress_logger = logging.getLogger("progress")
    progress_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    progress_logger.handlers = []
    
    # Create file handler
    log_file = run_dir / "progress.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    progress_logger.addHandler(file_handler)
    
    return progress_logger

def setup_error_logger(run_dir):
    """
    Set up a consolidated error logger.
    
    Args:
        run_dir: Path to the run directory
        
    Returns:
        Logger instance configured for error logging
    """
    error_logger = logging.getLogger("errors")
    error_logger.setLevel(logging.ERROR)
    
    # Remove existing handlers
    error_logger.handlers = []
    
    # Create file handler
    log_file = run_dir / "errors.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    error_logger.addHandler(file_handler)
    
    return error_logger
