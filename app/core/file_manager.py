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
from PyPDF2 import PdfReader, PdfWriter
import io

from app.config import (
    NEW_OFFERS_PATH,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    MAX_FILE_SIZE_MB,
    CLEANUP_DAYS
)

class FileManager:
    """Handles file operations for the application."""

    def __init__(self):
        """
        Initialize FileManager with directory paths and configuration.

        Args:
            new_dir (Path): Directory for new offer PDFs
            in_progress_dir (Path): Directory for offers being processed
            archived_dir (Path): Directory for archived/rejected offers
            max_file_size_mb (int): Maximum allowed file size in MB
            cleanup_days (int): Number of days after which archived files are deleted
        """
        # Initialize directories
        self.new_dir = NEW_OFFERS_PATH
        self.in_progress_dir = IN_PROGRESS_PATH
        self.archived_dir = ARCHIVED_PATH

        # Initialize configuration
        self.max_file_size_mb = MAX_FILE_SIZE_MB
        self.cleanup_days = CLEANUP_DAYS

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Log initialization paths
        self.logger.info(f"Initialized FileHandler with paths:")
        self.logger.info(f"New offers dir: {self.new_dir} (exists: {self.new_dir.exists()})")
        self.logger.info(f"In progress dir: {self.in_progress_dir} (exists: {self.in_progress_dir.exists()})")
        self.logger.info(f"Archived dir: {self.archived_dir} (exists: {self.archived_dir.exists()})")

        # Configuration
        self.logger.info(f"Max file size: {self.max_file_size_mb} MB")
        self.logger.info(f"Cleanup days: {self.cleanup_days}")

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
        # Convert file size to MB (1 MB = 1024 * 1024 bytes)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        return file_size_mb <= self.max_file_size_mb

    def compress_pdf(self, file_path: Path) -> Optional[Path]:
        """
        Compress PDF file if it exceeds size limit.

        Args:
            file_path (Path): Path to the PDF file

        Returns:
            Optional[Path]: Path to compressed file or None if compression failed
        """
        try:
            # Si le fichier est déjà dans la limite
            if self.validate_file_size(file_path):
                return file_path

            self.logger.info(f"Compressing file: {file_path}")

            # Lire le PDF
            reader = PdfReader(str(file_path))
            writer = PdfWriter()

            # Copier chaque page avec compression
            for page in reader.pages:
                writer.add_page(page)

            # Définir les paramètres de compression
            writer.add_metadata(reader.metadata)

            # Créer le nom du fichier compressé
            compressed_path = file_path.parent / f"compressed_{file_path.name}"

            # Sauvegarder le PDF compressé
            with open(compressed_path, "wb") as f:
                writer.write(f)

            # Vérifier si la compression a réussi
            if self.validate_file_size(compressed_path):
                self.logger.info(f"Successfully compressed {file_path.name}")
                # Supprimer l'original et renommer le compressé
                file_path.unlink()
                compressed_path.rename(file_path)
                return file_path
            else:
                self.logger.warning(f"Compression insufficient for {file_path.name}")
                compressed_path.unlink()
                return None

        except Exception as e:
            self.logger.error(f"Error compressing PDF: {e}")
            return None

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
                self.logger.info(f"File too large, attempting compression: {file_path}")
                compressed_file = self.compress_pdf(file_path)
                if not compressed_file:
                    self.logger.error(f"Compression failed: {file_path}")
                    return None
                file_path = compressed_file

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
