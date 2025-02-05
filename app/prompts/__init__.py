"""
Prompts package for the Claude API.

This package contains all prompts used by the analyzer for different operations.
"""

from .system import SYSTEM_PROMPT, CONTEXT_PROMPT
from .analysis import ANALYSIS_PROMPT, COMPANY_PROMPT
from .generation import GENERATION_PROMPT

__all__ = [
    'SYSTEM_PROMPT',
    'CONTEXT_PROMPT',
    'ANALYSIS_PROMPT',
    'COMPANY_PROMPT',
    'GENERATION_PROMPT'
]
