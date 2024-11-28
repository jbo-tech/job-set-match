"""
Helper modules for Job Set & Match!

This package contains utility modules for:
- Job offer analysis
- File management
- Data handling
"""

from .analyzer import OfferAnalyzer
from .data_handler import DataHandler
from .file_manager import FileManager
from .config import (
    OFFERS_PATH,
    NEW_OFFERS_PATH,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    DATA_PATH,
    ANALYSES_FILE,
    MAX_FILE_SIZE_MB,
    CLEANUP_DAYS
)

__all__ = [
    'OfferAnalyzer',
    'DataHandler',
    'FileManager',
    'OFFERS_PATH',
    'NEW_OFFERS_PATH',
    'IN_PROGRESS_PATH',
    'ARCHIVED_PATH',
    'DATA_PATH',
    'ANALYSES_FILE',
    'MAX_FILE_SIZE_MB',
    'CLEANUP_DAYS'
]
