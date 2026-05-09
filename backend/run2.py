import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

# Validate the import works
from backend.main import app
from backend.main import get_db_manager
print("get_db_manager import OK:", get_db_manager)

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
