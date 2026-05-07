import pytest
from family_agent.data_migration import DataMigrationManager
from pathlib import Path
import tempfile


def test_export_json():
    """Test JSON export"""
    manager = DataMigrationManager(data_dir="data")
    output = manager.export_all(format='json')
    assert isinstance(output, str)
    assert Path(output).exists()


def test_backup_and_restore(tmp_path):
    """Test backup and restore"""
    manager = DataMigrationManager(data_dir="data")
    backup_path = str(tmp_path / "backup.json")
    manager.backup_to_file(backup_path)
    assert Path(backup_path).exists()


def test_import_json(tmp_path):
    """Test JSON import"""
    manager = DataMigrationManager(data_dir="data")
    # Create test file
    test_file = tmp_path / "test_export.json"
    import json
    test_data = {"members": [], "shopping": []}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    result = manager.import_all(str(test_file), format='json')
    assert result is True
