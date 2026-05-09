import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

# Simulate what the auth route does
from backend.main import get_auth_manager as _get_auth

auth = _get_auth()
print("auth created:", type(auth).__name__)

info = auth.get_family_info("807325")
print("family:", info)

result = auth.login("我")
print("login:", result)
print("DONE")
