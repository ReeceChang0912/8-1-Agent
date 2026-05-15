import pytest
import os
from pathlib import Path


def test_env_example_no_real_keys():
    """Test that .env.example doesn't contain real API keys"""
    with open('config/.env.example', 'r', encoding='utf-8') as f:
        content = f.read()
    # Check no real-looking keys (simple check)
    assert 'sk-' not in content or 'your_' in content, ".env.example may contain real API keys"
    assert "DEEP" + "SEEK" + "_API_KEY=" + "sk-" not in content, "Real DeepSeek key in example"


def test_gitignore_includes_env():
    """Test that .gitignore includes local env files"""
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    assert '.env' in content, ".gitignore missing .env"
    assert 'config/.env' in content, ".gitignore missing config/.env"


def test_no_env_in_git_history():
    """Test no real .env file in git history"""
    import subprocess
    result = subprocess.run(['git', 'log', '--all', '--full-history', '--', 'config/.env'],
                          capture_output=True, text=True)
    # If no output, then .env was never committed
    assert len(result.stdout.strip()) == 0, "config/.env was committed to git history"


def test_source_has_no_hardcoded_database_url():
    """Test source files don't embed concrete database secrets."""
    source_roots = [Path("backend"), Path("family_agent"), Path("frontend/src"), Path("tests")]
    forbidden_markers = [
        "postgres." + "trhxvrcutwusuxodeppt",
        "NIMA" + "luobin",
        "DEEP" + "SEEK" + "_API_KEY=" + "sk-",
        "OSS_ACCESS_KEY_SECRET=" + "5Q",
    ]
    offenders = []
    for root in source_roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".js"}:
                content = path.read_text(encoding="utf-8", errors="ignore")
                if any(marker in content for marker in forbidden_markers):
                    offenders.append(str(path))
    assert offenders == [], f"Hardcoded secret found in source: {offenders}"
