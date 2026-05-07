"""
Data Migration Manager
Handles import/export of all family agent data
"""
from typing import Dict, List
from pathlib import Path
import json
import csv
import shutil
from datetime import datetime


class DataMigrationManager:
    """Manage data import/export"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_files = {
            'members': 'members.json',
            'shopping': 'shopping_list.json',
            'reminders': 'reminders.json',
            'chat_history': 'chat_history.json',
            'tasks': 'family_tasks.json'
        }

    def export_all(self, format: str = 'json', output_path: str = None) -> str:
        """
        Export all data
        Args:
            format: 'json' or 'csv'
            output_path: Output file path (optional)
        Returns:
            Path to exported file
        """
        all_data = {}
        for key, filename in self.data_files.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data[key] = json.load(f)
            else:
                all_data[key] = []

        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.data_dir / f"export_{timestamp}.json")

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        elif format == 'csv':
            # Simplified CSV export (only members as example)
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['type', 'data'])
                for key, data in all_data.items():
                    writer.writerow([key, json.dumps(data, ensure_ascii=False)])

        return output_path

    def import_all(self, file_path: str, format: str = 'json') -> bool:
        """
        Import data from file
        Args:
            file_path: Path to import file
            format: 'json' or 'csv'
        Returns:
            True if successful
        """
        try:
            if format == 'json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            elif format == 'csv':
                # Simplified CSV import
                all_data = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        all_data[row[0]] = json.loads(row[1])

            # Import each data type
            for key, data in all_data.items():
                if key in self.data_files:
                    file_path_obj = self.data_dir / self.data_files[key]
                    with open(file_path_obj, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception:
            return False

    def backup_to_file(self, backup_path: str):
        """Backup all data to a single file"""
        self.export_all(format='json', output_path=backup_path)

    def restore_from_file(self, backup_path: str) -> bool:
        """Restore data from backup file"""
        return self.import_all(backup_path, format='json')
