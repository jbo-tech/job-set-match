"""
Data handler for Claude API responses in Job Set & Match!

This module handles:
- Storing and retrieving Claude API analysis results
- Tracking API usage costs
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

class DataHandler:
    """Handles Claude API data operations."""

    def __init__(self, data_file: Path):
        """
        Initialize DataHandler with data file path.

        Args:
            data_file (Path): Path to the JSON data file
        """
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize or load data
        self.data = self._load_or_initialize()

    def _load_or_initialize(self) -> Dict:
        """
        Load existing data or initialize new data structure.

        Returns:
            Dict: Application data structure
        """
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                self.logger.error(f"Error loading data file: {e}")
                return self._initialize_data()
        return self._initialize_data()

    def _initialize_data(self) -> Dict:
        """
        Initialize empty data structure.

        Returns:
            Dict: Empty data structure with API usage tracking and analyses list
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "analyses": [{
                "timestamp": datetime.now().isoformat(),
                "offers": []
            }],
            "api_usage": {
                "total_cost": 0.0,
                "analysis_costs": 0.0,
                "cover_letter_costs": 0.0,
                "requests_count": 0
            }
        }

    def save(self) -> bool:
        """
        Save current data to file.

        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            return False

    def add_analysis(self, analysis: Dict) -> bool:
        """
        Add new analysis result and update API costs.

        Args:
            analysis (Dict): Analysis result from Claude API

        Returns:
            bool: True if addition successful, False otherwise
        """
        try:
            # Add analysis to the latest batch
            self.data["analyses"][-1]["offers"].append(analysis)
            self.data["api_usage"]["analysis_costs"] += analysis.get("analysis_cost", 0.0)
            self.data["api_usage"]["total_cost"] += analysis.get("analysis_cost", 0.0)
            self.data["api_usage"]["requests_count"] += 1
            self.data["timestamp"] = datetime.now().isoformat()
            return self.save()
        except Exception as e:
            self.logger.error(f"Error adding analysis: {e}")
            return False

    def add_cover_letter_cost(self, cost: float) -> bool:
        """
        Update API usage with cover letter generation cost.

        Args:
            cost (float): Cost of generating the cover letter

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.data["api_usage"]["cover_letter_costs"] += cost
            self.data["api_usage"]["total_cost"] += cost
            self.data["api_usage"]["requests_count"] += 1
            self.data["timestamp"] = datetime.now().isoformat()
            return self.save()
        except Exception as e:
            self.logger.error(f"Error adding cover letter cost: {e}")
            return False

    def get_analysis(self, file_name: str) -> Optional[Dict]:
        """
        Get specific analysis by file name from the latest batch.

        Args:
            file_name (str): File name to identify the analysis

        Returns:
            Optional[Dict]: Analysis data if found, None otherwise
        """
        try:
            for offer in self.data["analyses"][-1]["offers"]:
                if offer["file_name"] == file_name:
                    return offer
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving analysis: {e}")
            return None

    def get_all_analyses(self) -> List[Dict]:
        """
        Get all analyses from the latest batch.

        Returns:
            List[Dict]: List of all analyses in the current batch
        """
        try:
            if not self.data["analyses"]:  # If the list is empty
                return []
            return self.data["analyses"][-1]["offers"]
        except (IndexError, KeyError):  # Handle possible errors
            return []

    def get_api_usage(self) -> Dict:
        """
        Get API usage statistics.

        Returns:
            Dict: API usage data including costs and request counts
        """
        return self.data["api_usage"]

    def clear_analyses(self, batch: str = "all") -> bool:
        """
        Clear current batch of analyses and start a new one.
        Preserves API usage statistics.

        Args:
            batch (str, optional): Batch type to clear. Defaults to "All".
                - "last": Clear only the last batch
                - "All": Clear all batches and start fresh

        Returns:
            bool: True if clearing successful, False otherwise
        """
        try:
            if batch == "last":
                # Create new batch
                self.data["analyses"][-1].append({
                    "timestamp": datetime.now().isoformat(),
                    "offers": []
                })
            else:
                # Create new batch
                self.data["analyses"].append({
                    "timestamp": datetime.now().isoformat(),
                    "offers": []
                })
            self.data["timestamp"] = datetime.now().isoformat()
            return self.save()
        except Exception as e:
            self.logger.error(f"Error clearing analyses: {e}")
            return False
