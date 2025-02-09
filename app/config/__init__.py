"""
Configuration package for Job Set & Match!

This package exposes all configuration settings and paths in a centralized way.
"""

from .paths import (
    BASE_DIR,
    OFFERS_PATH,
    NEW_OFFERS_PATH,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    DATA_PATH,
    CONTEXT_PATH,
    ANALYSES_PATH,
    ANALYSES_FILE
)

from .settings import (
    MAX_FILE_SIZE_MB,
    CLEANUP_DAYS,
    ANTHROPIC_API_KEY,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    COVER_LETTER_TEMPERATURE,
    TOKEN_COST,
    PREFERRED_STORAGE,
    BATCH_POLLING_INTERVAL,
    BATCH_MAX_SIZE,
    init_config
)

__all__ = [
    # Paths
    'BASE_DIR',
    'OFFERS_PATH',
    'NEW_OFFERS_PATH',
    'IN_PROGRESS_PATH',
    'ARCHIVED_PATH',
    'DATA_PATH',
    'CONTEXT_PATH',
    'ANALYSES_PATH',
    'ANALYSES_FILE',
    # Settings
    'MAX_FILE_SIZE_MB',
    'CLEANUP_DAYS',
    'ANTHROPIC_API_KEY',
    'DEFAULT_MODEL',
    'DEFAULT_MAX_TOKENS',
    'DEFAULT_TEMPERATURE',
    'COVER_LETTER_TEMPERATURE',
    'TOKEN_COST',
    'PREFERRED_STORAGE',
    'BATCH_POLLING_INTERVAL',
    'BATCH_MAX_SIZE',
    'init_config'
]
