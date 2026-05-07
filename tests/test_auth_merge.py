import pytest
import os


def test_single_auth_module_exists():
    """Test that only one auth module exists"""
    assert os.path.exists('family_agent/family_auth.py'), "family_auth.py should exist"
    assert not os.path.exists('family_agent/auth_manager.py'), "auth_manager.py should be merged and deleted"


def test_family_auth_has_all_auth_functions():
    """Test that family_auth has all necessary auth functions"""
    from family_agent.family_auth import FamilyAuthManager
    manager = FamilyAuthManager()
    # Check key methods exist
    assert hasattr(manager, 'create_family'), "Missing create_family"
    assert hasattr(manager, 'join_family'), "Missing join_family"
    assert hasattr(manager, 'login'), "Missing login"


def test_core_no_auth_manager_import():
    """Test that core.py doesn't import auth_manager"""
    with open('family_agent/core.py', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'auth_manager' not in content, "core.py should not import auth_manager"
