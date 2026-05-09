import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

from backend.main import get_db_manager, get_agent, get_auth_manager

print("1. get_db_manager...")
db = get_db_manager()
print("   OK:", type(db).__name__)

print("2. get_auth_manager...")
auth = get_auth_manager()
print("   OK:", type(auth).__name__)

print("3. get_family_info...")
info = auth.get_family_info("807325")
print("   Result:", info)

print("4. login...")
result = auth.login("我")
print("   Result:", result)

print("\nAll checks passed!")
