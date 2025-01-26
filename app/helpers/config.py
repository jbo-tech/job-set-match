from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Constants paths
OFFERS_PATH = Path("offers")
NEW_OFFERS_PATH = OFFERS_PATH / "0_new"
IN_PROGRESS_PATH = OFFERS_PATH / "1_in_progress"
ARCHIVED_PATH = OFFERS_PATH / "2_archived"
DATA_PATH = Path("data")
ANALYSES_FILE = DATA_PATH / "analyses.json"

# Environment configs with defaults
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 10))
CLEANUP_DAYS = int(os.getenv('CLEANUP_DAYS', 30))

# Ensure directories exist
for path in [NEW_OFFERS_PATH, IN_PROGRESS_PATH, ARCHIVED_PATH, DATA_PATH]:
    path.mkdir(parents=True, exist_ok=True)
