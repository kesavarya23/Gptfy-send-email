"""
Data Loader Module
Handles loading opportunity and case data from JSON and CSV files
"""

import json
import csv
# import pandas as pd
from typing import List, Dict
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load Salesforce data from files"""

    @staticmethod
    def load_from_json(file_path: str) -> List[Dict]:
        """
        Load data from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            List of dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} records from {file_path}")
                return data
            elif isinstance(data, dict):
                logger.info(f"Loaded 1 record from {file_path}")
                return [data]
            else:
                logger.error(f"Invalid JSON format in {file_path}")
                return []

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {str(e)}")
            return []

    @staticmethod
    def load_from_csv(file_path: str) -> List[Dict]:
        """
        Load data from CSV file

        Args:
            file_path: Path to CSV file

        Returns:
            List of dictionaries
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.DictReader(f)
                data = list(reader)
            # Replace NaN with empty strings
            df = df.fillna('')
            data = df.to_dict('records')
            logger.info(f"Loaded {len(data)} records from {file_path}")
            return data

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading CSV from {file_path}: {str(e)}")
            return []

    @staticmethod
    def save_to_json(data: List[Dict], file_path: str) -> bool:
        """
        Save data to JSON file

        Args:
            data: List of dictionaries to save
            file_path: Path to save JSON file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(data)} records to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {str(e)}")
            return False

    @staticmethod
    def save_to_csv(data: List[Dict], file_path: str) -> bool:
        """
        Save data to CSV file

        Args:
            data: List of dictionaries to save
            file_path: Path to save CSV file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)

            logger.info(f"Saved {len(data)} records to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving CSV to {file_path}: {str(e)}")
            return False

    @staticmethod
    def validate_opportunity_data(data: Dict) -> bool:
        """
        Validate that required fields exist for opportunity data

        Args:
            data: Dictionary with opportunity data

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['opportunity_name', 'stage', 'close_date']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        return True

    @staticmethod
    def validate_case_data(data: Dict) -> bool:
        """
        Validate that required fields exist for case data

        Args:
            data: Dictionary with case data

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['case_number', 'subject', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        return True
