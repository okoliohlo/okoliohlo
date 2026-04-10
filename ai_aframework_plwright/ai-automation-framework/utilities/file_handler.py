"""
File Handler
Utilities for file operations
"""

import json
import yaml
import csv
from pathlib import Path
from typing import Any, Dict, List
from utilities.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Handles file operations"""

    @staticmethod
    def read_json(file_path: Path) -> Dict:
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON file {file_path}: {str(e)}")
            raise

    @staticmethod
    def write_json(file_path: Path, data: Dict, indent: int = 2):
        """Write JSON file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"JSON file written: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write JSON file {file_path}: {str(e)}")
            raise

    @staticmethod
    def read_yaml(file_path: Path) -> Dict:
        """Read YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read YAML file {file_path}: {str(e)}")
            raise

    @staticmethod
    def write_yaml(file_path: Path, data: Dict):
        """Write YAML file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
            logger.info(f"YAML file written: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write YAML file {file_path}: {str(e)}")
            raise

    @staticmethod
    def read_csv(file_path: Path) -> List[Dict]:
        """Read CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            logger.error(f"Failed to read CSV file {file_path}: {str(e)}")
            raise

    @staticmethod
    def write_csv(file_path: Path, data: List[Dict], fieldnames: List[str] = None):
        """Write CSV file"""
        try:
            if not data:
                logger.warning("No data to write to CSV")
                return

            file_path.parent.mkdir(parents=True, exist_ok=True)

            fieldnames = fieldnames or list(data[0].keys())

            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"CSV file written: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write CSV file {file_path}: {str(e)}")
            raise