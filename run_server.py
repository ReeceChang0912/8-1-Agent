"""Start the backend server with correct environment"""
import os, sys

# Must be set BEFORE any imports
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

# Now import and start
from backend.main import app
import uvicorn

config = uvicorn.Config(app, host="0.0.0.0", port=8000, http="h11", loop="asyncio")
server = uvicorn.Server(config)
server.run()
