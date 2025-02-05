"""
Path configurations for Job Set & Match!

This module centralizes all path-related configurations.
"""

from pathlib import Path
import os

# Base path calculations - detect Docker environment by checking path
BASE_DIR = Path(__file__).parent.parent.parent

# Offer-related paths
OFFERS_PATH = BASE_DIR / "offers"
NEW_OFFERS_PATH = OFFERS_PATH / "0_new"
IN_PROGRESS_PATH = OFFERS_PATH / "1_in_progress"
ARCHIVED_PATH = OFFERS_PATH / "2_archived"

# Data paths
DATA_PATH = BASE_DIR / "data"
CONTEXT_PATH = DATA_PATH / "context"
ANALYSES_PATH = DATA_PATH / "analyses"
ANALYSES_FILE = ANALYSES_PATH / "analyses.json"

# Ensure all required directories exist
REQUIRED_PATHS = [
    OFFERS_PATH,
    NEW_OFFERS_PATH,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    DATA_PATH,
    CONTEXT_PATH,
    ANALYSES_PATH,
]

for path in REQUIRED_PATHS:
    path.mkdir(parents=True, exist_ok=True)

# Ensure all directories exist
def ensure_paths():
    """Create all required directories if they don't exist."""
    paths = [BASE_DIR, ANALYSES_PATH]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
