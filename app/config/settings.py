"""
Global settings configuration for Job Set & Match!

This module centralizes all settings and environment configurations.
"""

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# File processing configurations
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 10))
CLEANUP_DAYS = int(os.getenv('CLEANUP_DAYS', 30))

# Batch processing configuration
BATCH_MAX_SIZE = 100  # Maximum number of requests per batch
BATCH_POLLING_INTERVAL = 5  # Seconds between polling for batch status

# API configurations
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Model configurations
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.2
COVER_LETTER_TEMPERATURE = 0.7

# Cost tracking
TOKEN_COST = 0.00001  # Cost per token

# Preferred storage configuration
PREFERRED_STORAGE = os.getenv('PREFERRED_STORAGE', 'parquet').lower()

# Initialize configuration
def init_config():
    """Validate and initialize configuration."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    return {
        'max_file_size_mb': MAX_FILE_SIZE_MB,
        'cleanup_days': CLEANUP_DAYS,
        'api_key': ANTHROPIC_API_KEY,
        'model': DEFAULT_MODEL,
        'max_tokens': DEFAULT_MAX_TOKENS,
        'temperature': DEFAULT_TEMPERATURE,
        'cover_letter_temperature': COVER_LETTER_TEMPERATURE,
        'token_cost': TOKEN_COST,
        'preferred_storage': PREFERRED_STORAGE
    }
