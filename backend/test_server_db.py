import sys
sys.path = ['.', '..'] + sys.path
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

# Direct test - does the env var work?
from family_agent.database import DatabaseManager
try:
    db = DatabaseManager()
    print('DIRECT CONNECT OK')
    db.close()
except Exception as e:
    print(f'DIRECT CONNECT FAILED: {e}')

# Now simulate what the server does
from backend.main import get_db_manager, get_auth_manager
print('Import OK')

db2 = get_db_manager()
print(f'get_db_manager result: {db2}')

if db2:
    auth = get_auth_manager()
    print(f'auth.db: {auth.db}')
    print(f'families: {db2.get_all_families()}')
else:
    print('DB is None - backend issue')
