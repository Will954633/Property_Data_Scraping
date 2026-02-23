# Last Edit: 01/02/2026, Saturday, 7:14 am (Brisbane Time)
# Configuration module for Ollama-based property analysis system
# Processes properties from Gold_Coast_Currently_For_Sale database
# Target suburbs: Robina, Mudgeeraba, Varsity Lakes, Reedy Creek, Burleigh Waters, Merrimac, Worongary
# FIXED: Corrected suburb names to match database collection names (underscores for multi-word, correct spellings)

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "Gold_Coast_Currently_For_Sale"
COLLECTION_NAME = "properties"

# Target Suburbs - Collection names (must match database exactly: underscores for multi-word suburbs)
# TESTING MODE: Only Robina for rapid feedback
# To re-enable all suburbs, uncomment the other lines
TARGET_SUBURBS = [
    "robina",
    # TESTING: Temporarily disabled - uncomment after testing
    # "mudgeeraba",
    # "varsity_lakes",      # Fixed: was "varsity lakes"
    # "reedy_creek",        # Fixed: was "reedy creek"
    # "burleigh_waters",    # Fixed: was "burleigh waters"
    # "merrimac",           # Fixed: was "merimac" (spelling correction)
    # "worongary"           # Fixed: was "warongary" (spelling correction)
]

# OpenAI Configuration (Primary LLM for all visual analysis)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano-2025-08-07")
OPENAI_TIMEOUT = 120  # 2 minutes for OpenAI requests
MAX_TOKENS = 16000
TEMPERATURE = 0.1  # Low temperature for consistent, factual responses

# Ollama Configuration (DEPRECATED - no longer used)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = "gpt-5-nano-2025-08-07"  # Unused - OpenAI is primary
OLLAMA_TIMEOUT = 120
OPENAI_FALLBACK_ENABLED = False
USE_OPENAI_PRIMARY = True  # Always use OpenAI

# Processing Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))

# Image Processing
MAX_IMAGES_PER_PROPERTY = int(os.getenv("MAX_IMAGES_PER_PROPERTY", "5"))  # Very conservative for Ollama
IMAGE_DETAIL_LEVEL = "auto"  # Ollama handles this automatically
# Process images one at a time to avoid payload size issues
PROCESS_IMAGES_INDIVIDUALLY = True

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/ollama_processing.log"

# Paths
LOG_DIR = "logs/"
OUTPUT_DIR = "output/"

# Parallel Processing Configuration
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "2"))  # Conservative for Ollama
PARALLEL_BATCH_SIZE = int(os.getenv("PARALLEL_BATCH_SIZE", "50"))
WORKER_HEARTBEAT_INTERVAL = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "60"))
WORKER_TIMEOUT = int(os.getenv("WORKER_TIMEOUT", "600"))  # 10 minutes for Ollama
ENABLE_WORKER_LOGS = os.getenv("ENABLE_WORKER_LOGS", "True").lower() == "true"
ENABLE_PROGRESS_LOG = os.getenv("ENABLE_PROGRESS_LOG", "True").lower() == "true"

# Testing Configuration
TEST_RUN = os.getenv("TEST_RUN", "True").lower() == "true"
MAX_BATCHES = int(os.getenv("MAX_BATCHES", "2"))  # 0 = unlimited, >0 = limit for testing

# Ensure directories exist
for directory in [LOG_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)
