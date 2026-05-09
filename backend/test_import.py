import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'
print("1. importing backend.main...")
from backend.main import app
print("2. importing get_db_manager...")
from backend.main import get_db_manager
print("3. OK:", type(get_db_manager))
