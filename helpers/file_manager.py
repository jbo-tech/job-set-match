"""
File management utilities for Job Set & Match!

This module handles all file operations including:
- PDF file movement between directories
- File standardization
- File validation
"""

import shutil
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Optional
import re

class FileManager:
    """Handles file operations for the application."""

    def __init__(self, new_dir: Path, in_progress_dir: Path, archived_dir: Path,
                 max_file_size_mb: int = 10, cleanup_days: int = 30):
        """
        Initialize FileManager with directory paths and configuration.

        Args:
            new_dir (Path): Directory for new offer PDFs
            in_progress_dir (Path): Directory for offers being processed
            archived_dir (Path): Directory for archived/rejected offers
            max_file_size_mb (int): Maximum allowed file size in MB
            cleanup_days (int): Number of days after which archived files are deleted
        """
        self.new_dir = new_dir
        self.in_progress_dir = in_progress_dir
        self.archived_dir = archived_dir
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.cleanup_days = cleanup_days

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_new_offers(self) -> List[Path]:
        """
        Get list of new offer PDFs to analyze.

        Returns:
            List[Path]: List of PDF files in the new offers directory
        """
        return list(self.new_dir.glob("*.pdf"))

    def validate_file_size(self, file_path: Path) -> bool:
        """
        Check if file size is within the allowed limit.

        Args:
            file_path (Path): Path to the file to check

        Returns:
            bool: True if file size is valid, False otherwise
        """
        return file_path.stat().st_size <= self.max_file_size_bytes

    def standardize_filename(self, file_path: Path, company: str, position: str) -> Path:
        """
        Create standardized filename from analysis results.

        Args:
            file_path (Path): Original file path
            company (str): Company name from analysis
            position (str): Position title from analysis

        Returns:
            Path: New path with standardized filename
        """
        # Clean and format company and position
        company = re.sub(r'[^\w\s-]', '', company.lower()).replace(' ', '_')
        position = re.sub(r'[^\w\s-]', '', position.lower()).replace(' ', '_')
        date = datetime.now().strftime('%Y%m%d%H%M%S')

        # Create new filename
        new_name = f"{company}_{position}_{date}.pdf"
        return file_path.parent / new_name

    def move_to_in_progress(self, file_path: Path) -> Optional[Path]:
        """
        Move a file to the in_progress directory.

        Args:
            file_path (Path): Path to the file to move

        Returns:
            Optional[Path]: New path of the moved file, or None if move failed
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None

            if not self.validate_file_size(file_path):
                self.logger.error(f"File too large: {file_path}")
                return None

            new_path = self.in_progress_dir / file_path.name
            shutil.move(str(file_path), str(new_path))
            self.logger.info(f"Moved {file_path.name} to in_progress directory")
            return new_path
        except Exception as e:
            self.logger.error(f"Error moving file to in_progress: {e}")
            return None

    def move_to_archived(self, file_path: Path) -> Optional[Path]:
        """
        Move a file to the archived directory.

        Args:
            file_path (Path): Path to the file to archive

        Returns:
            Optional[Path]: New path of the archived file, or None if move failed
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None

            new_path = self.archived_dir / file_path.name
            shutil.move(str(file_path), str(new_path))
            self.logger.info(f"Moved {file_path.name} to archived directory")
            return new_path
        except Exception as e:
            self.logger.error(f"Error moving file to archived: {e}")
            return None

    def rename_after_analysis(self, file_path: Path, company: str, position: str) -> Optional[Path]:
        """
        Rename file using standardized format after analysis.

        Args:
            file_path (Path): Current file path
            company (str): Company name from analysis
            position (str): Position title from analysis

        Returns:
            Optional[Path]: New path with standardized name, or None if rename failed
        """
        try:
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return None

            new_path = self.standardize_filename(file_path, company, position)
            file_path.rename(new_path)
            self.logger.info(f"Renamed {file_path.name} to {new_path.name}")
            return new_path
        except Exception as e:
            self.logger.error(f"Error renaming file: {e}")
            return None

    def cleanup_old_files(self) -> None:
        """Remove files older than cleanup_days from archived directory."""
        try:
            cutoff = datetime.now().timestamp() - (self.cleanup_days * 24 * 60 * 60)
            for file_path in self.archived_dir.glob("*.pdf"):
                if file_path.stat().st_mtime < cutoff:
                    file_path.unlink()
                    self.logger.info(f"Removed old file: {file_path.name}")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
