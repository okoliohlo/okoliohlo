"""
Test Execution Tracker
Tracks test execution metrics and results
"""

import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class TestTracker:
    """Tracks test execution data"""

    def __init__(self):
        self.execution_data = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'environment': config.environment,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'duration': 0,
            'test_results': [],
            'failure_categories': defaultdict(int),
        }
        self.data_file = config.reports_dir / "test_execution_data.json"

    def record_test_start(self, test_name: str, test_id: str = None):
        """Record test start"""
        logger.info(f"Test started: {test_name}")
        self.execution_data['total_tests'] += 1

    def record_test_result(self, test_name: str, status: str, duration: float,
                           error_message: str = None, category: str = None):
        """
        Record test result

        Args:
            test_name: Test name
            status: Test status (passed, failed, skipped)
            duration: Test duration in seconds
            error_message: Error message if failed
            category: Failure category
        """
        result = {
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'error_message': error_message,
            'category': category
        }

        self.execution_data['test_results'].append(result)

        # Update counters
        if status == 'passed':
            self.execution_data['passed'] += 1
        elif status == 'failed':
            self.execution_data['failed'] += 1
            if category:
                self.execution_data['failure_categories'][category] += 1
        elif status == 'skipped':
            self.execution_data['skipped'] += 1
        elif status == 'error':
            self.execution_data['errors'] += 1

        logger.info(f"Test result recorded: {test_name} - {status}")

    def finalize(self):
        """Finalize execution data"""
        self.execution_data['end_time'] = datetime.now().isoformat()

        # Calculate total duration
        start = datetime.fromisoformat(self.execution_data['start_time'])
        end = datetime.fromisoformat(self.execution_data['end_time'])
        self.execution_data['duration'] = (end - start).total_seconds()

        # Calculate pass rate
        total = self.execution_data['total_tests']
        passed = self.execution_data['passed']
        self.execution_data['pass_rate'] = (passed / total * 100) if total > 0 else 0

        # Save to file
        self._save_to_file()

        logger.info("Test execution data finalized")

    def _save_to_file(self):
        """Save execution data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.execution_data, f, indent=2, default=str)
            logger.info(f"Execution data saved: {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save execution data: {str(e)}")

    def get_summary(self) -> Dict:
        """Get execution summary"""
        return {
            'total': self.execution_data['total_tests'],
            'passed': self.execution_data['passed'],
            'failed': self.execution_data['failed'],
            'skipped': self.execution_data['skipped'],
            'pass_rate': self.execution_data.get('pass_rate', 0),
            'duration': self.execution_data.get('duration', 0)
        }


# Global tracker instance
tracker = TestTracker()