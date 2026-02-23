"""
Configuration module for floor plan data extraction system.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
# Allow overriding via environment variables while keeping existing defaults
DATABASE_NAME = os.getenv("DATABASE_NAME", "property_data")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "properties_for_sale")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-5-nano-2025-08-07"  # As specified in requirements
MAX_TOKENS = 16000
TEMPERATURE = 0.1  # Low temperature for consistent, factual responses

# Processing Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/floor_plan_processing.log"

# Paths
LOG_DIR = "logs/"
OUTPUT_DIR = "output/"

# Ensure directories exist
for directory in [LOG_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)
