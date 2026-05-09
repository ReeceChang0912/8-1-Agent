import sys, os
sys.path = ['..', '.'] + sys.path
os.chdir('..')

# Simulate what backend/main.py does
_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
print(f".env path: {_env_path}")
print(f".env exists: {os.path.exists(_env_path)}")

if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

print(f"DATABASE_URL = '{os.environ.get('DATABASE_URL', 'NOT SET')}'")
print(f"Length: {len(os.environ.get('DATABASE_URL', ''))}")

from family_agent.database import DatabaseManager
db = DatabaseManager()
print('DB OK')
db.close()
