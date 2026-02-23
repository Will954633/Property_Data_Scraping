"""
Configuration module for GPT enrichment pipeline.
Last Edit: 13/02/2026, 3:25 PM (Thursday) — Brisbane Time

Description: Central configuration for all enrichment components including
API keys, MongoDB settings, processing parameters, and logging configuration.

Edit History:
- 13/02/2026 3:25 PM: Initial creation for production pipeline
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# ============================================================================
# API CONFIGURATION
# ============================================================================

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-5-nano-2025-08-07"
MAX_TOKENS = 16000
REQUEST_TIMEOUT = 120  # seconds

# Google Maps API
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================

# Azure Cosmos DB (MongoDB API)
MONGODB_CONNECTION_STRING = os.getenv("COSMOS_CONNECTION_STRING")
COSMOS_CONNECTION_STRING = MONGODB_CONNECTION_STRING  # Alias for compatibility
DATABASE_NAME = "Gold_Coast_Currently_For_Sale"

# Collection names for 8 target suburbs (lowercase with underscores to match uploader)
SUBURB_COLLECTIONS = [
    "robina",
    "mudgeeraba",
    "varsity_lakes",
    "carrara",
    "reedy_creek",
    "burleigh_waters",
    "merrimac",
    "worongary"
]

# Alias for compatibility
TARGET_SUBURBS = SUBURB_COLLECTIONS

# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================

# Parallel processing
NUM_WORKERS = 10
WORKER_STAGGER_DELAY = 30  # seconds between worker starts
BATCH_SIZE = 240  # properties per worker (2400 / 10)

# Retry logic
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # exponential backoff base (seconds)

# Rate limiting
OSM_RATE_LIMIT_DELAY = 1  # seconds between OSM Nominatim requests
GOOGLE_MAPS_RATE_LIMIT_DELAY = 0.1  # seconds between Google Maps requests

# Image selection
MAX_IMAGES_PER_PROPERTY = 5
PREFERRED_IMAGE_DOMAIN = "rimh2.domainstatic.com"

# ============================================================================
# ENRICHMENT FIELDS CONFIGURATION
# ============================================================================

# Fields to enrich (all enabled by default)
ENRICHMENT_FIELDS = {
    "building_condition": True,
    "building_age": True,
    "busy_road": True,
    "corner_block": True,
    "parking": True,
    "outdoor_entertainment": True,
    "renovation_status": True
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log directory
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log files
MAIN_LOG_FILE = LOG_DIR / "enrichment.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
PROGRESS_LOG_FILE = LOG_DIR / "progress.log"

# Log levels
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

# Output directory for results
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Results files
RESULTS_FILE = OUTPUT_DIR / "enrichment_results.json"
FAILED_PROPERTIES_FILE = OUTPUT_DIR / "failed_properties.json"
SUMMARY_FILE = OUTPUT_DIR / "enrichment_summary.json"

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set in environment")
    
    if not MONGODB_CONNECTION_STRING:
        errors.append("COSMOS_CONNECTION_STRING not set in environment")
    
    if not GOOGLE_MAPS_API_KEY:
        errors.append("GOOGLE_PLACES_API_KEY not set (corner block will use GPT only)")
    
    if errors:
        print("⚠️  Configuration warnings:")
        for error in errors:
            print(f"   - {error}")
        
        # Only fail on critical errors
        if not OPENAI_API_KEY or not MONGODB_CONNECTION_STRING:
            raise ValueError("Critical configuration missing. Check .env file.")
    
    return True


# Validate on import
if __name__ != "__main__":
    validate_config()
