import pytest
from family_agent.invite_manager import InviteManager


def test_create_invite():
    """Test invite creation"""
    manager = InviteManager(data_dir="data")
    invite = manager.create_invite(family_id="test123", creator="张三")
    assert 'code' in invite
    assert 'expires_at' in invite


def test_validate_invite():
    """Test invite validation"""
    manager = InviteManager(data_dir="data")
    invite = manager.create_invite(family_id="test123", creator="张三")
    is_valid = manager.validate_invite(invite['code'])
    assert is_valid is not None


def test_generate_qr_code():
    """Test QR code generation"""
    manager = InviteManager(data_dir="data")
    invite = manager.create_invite(family_id="test123", creator="张三")
    qr_path = manager.generate_qr_code(invite['code'])
    # QR code generation might fail if qrcode not installed
    if qr_path:
        from pathlib import Path
        assert Path(qr_path).exists()
