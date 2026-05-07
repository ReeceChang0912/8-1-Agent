import pytest
import os
from pathlib import Path


def test_core_no_hardcoded_paths():
    """Test that core.py doesn't contain hardcoded D:/myAgent"""
    with open('family_agent/core.py', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'D:/myAgent' not in content, "Hardcoded D:/myAgent path found in core.py"


def test_role_manager_no_hardcoded_paths():
    """Test that role_manager.py doesn't contain hardcoded D:/myAgent"""
    with open('family_agent/role_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'D:/myAgent' not in content, "Hardcoded D:/myAgent path found in role_manager.py"


def test_pyproject_no_hardcoded_paths():
    """Test that pyproject.toml doesn't contain hardcoded D:/myAgent"""
    with open('pyproject.toml', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'D:/myAgent' not in content, "Hardcoded D:/myAgent path found in pyproject.toml"


def test_core_uses_relative_paths():
    """Test that core.py uses Path for data_dir"""
    with open('family_agent/core.py', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Path' in content or 'pathlib' in content, "Should use pathlib.Path"
