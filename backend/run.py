import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

import uvicorn
from backend.main import app
print("Starting uvicorn on port 8000...")
uvicorn.run(app, host="0.0.0.0", port=8000)
