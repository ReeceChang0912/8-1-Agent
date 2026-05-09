import sys, os
sys.path.insert(0, '..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'
from family_agent.database import DatabaseManager
db = DatabaseManager()
print('DB OK')
print('families:', db.get_all_families())
db.close()
