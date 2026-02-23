"""
Configuration module for property valuation data extraction system.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "Fetcha_Addresses")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "robina")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-5-nano-2025-08-07"  # As specified in SYSTEM_PLAN.md
# Separate, overrideable model for photo reordering so we can avoid
# model-specific issues (e.g. reasoning-only completions) without
# affecting the main valuation pipeline.
GPT_REORDER_MODEL = os.getenv("GPT_REORDER_MODEL", GPT_MODEL)
MAX_TOKENS = 16000  # Increased to accommodate full property analysis response
TEMPERATURE = 0.1  # Low temperature for consistent, factual responses

# Processing Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

# Test Mode Configuration
TEST_MODE = os.getenv("TEST_MODE", "True").lower() == "true"
STOP_AT_FIRST_HOUSE_PLAN = os.getenv("STOP_AT_FIRST_HOUSE_PLAN", "True").lower() == "true"

# Image Processing
MAX_IMAGES_PER_PROPERTY = int(os.getenv("MAX_IMAGES_PER_PROPERTY", "50"))
IMAGE_DOWNLOAD_TIMEOUT = int(os.getenv("IMAGE_DOWNLOAD_TIMEOUT", "30"))
SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".webp"]

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/processing.log"
SAVE_PROCESSED_DATA = True
DATA_EXPORT_DIR = "output/"

# Paths
TEMP_DIR = "temp/"
OUTPUT_DIR = "output/"
LOG_DIR = "logs/"

# Parallel Processing Configuration
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "3"))  # Default to 3 for testing
PARALLEL_BATCH_SIZE = int(os.getenv("PARALLEL_BATCH_SIZE", "100"))  # Documents per batch
BATCHES_PER_WORKER = int(os.getenv("BATCHES_PER_WORKER", "10"))  # Initial batches assigned per worker
WORKER_HEARTBEAT_INTERVAL = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "60"))  # Seconds
WORKER_TIMEOUT = int(os.getenv("WORKER_TIMEOUT", "300"))  # 5 minutes
ENABLE_WORKER_LOGS = os.getenv("ENABLE_WORKER_LOGS", "True").lower() == "true"
ENABLE_PROGRESS_LOG = os.getenv("ENABLE_PROGRESS_LOG", "True").lower() == "true"
WORKER_STARTUP_DELAY = int(os.getenv("WORKER_STARTUP_DELAY", "0"))  # Seconds between worker startups

# Testing Configuration for Parallel Mode
TEST_RUN = os.getenv("TEST_RUN", "True").lower() == "true"  # Run in test mode initially
MAX_BATCHES = int(os.getenv("MAX_BATCHES", "5"))  # 0 = unlimited, >0 = limit for testing

# Ensure directories exist
for directory in [TEMP_DIR, OUTPUT_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)
