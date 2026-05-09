import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'
from family_agent.family_auth import FamilyAuthManager
from family_agent.database import DatabaseManager
db = DatabaseManager()
auth = FamilyAuthManager(db_manager=db, data_dir="data")
info = auth.get_family_info("807325")
print("Family info:", info)
result = auth.login("我")
print("Login result:", result)
db.close()
