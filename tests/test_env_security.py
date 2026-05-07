import pytest
import os


def test_env_example_no_real_keys():
    """Test that .env.example doesn't contain real API keys"""
    with open('config/.env.example', 'r', encoding='utf-8') as f:
        content = f.read()
    # Check no real-looking keys (simple check)
    assert 'sk-' not in content or 'your_' in content, ".env.example may contain real API keys"
    assert 'DEEPSEEK_API_KEY=sk-' not in content, "Real DeepSeek key in example"


def test_gitignore_includes_env():
    """Test that .gitignore includes config/.env"""
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'config/.env' in content, ".gitignore missing config/.env"


def test_no_env_in_git_history():
    """Test no real .env file in git history"""
    import subprocess
    result = subprocess.run(['git', 'log', '--all', '--full-history', '--', 'config/.env'],
                          capture_output=True, text=True)
    # If no output, then .env was never committed
    assert len(result.stdout.strip()) == 0, "config/.env was committed to git history"
