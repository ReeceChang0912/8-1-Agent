"""Simple launcher that sets env and starts uvicorn"""
import os, sys, subprocess

os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'

# Start uvicorn as subprocess with env inherited
env = os.environ.copy()

proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'backend.main:app',
     '--host', '0.0.0.0', '--port', '8000',
     '--http', 'h11', '--loop', 'asyncio'],
    env=env
)

print(f"Started PID: {proc.pid}")
proc.wait()
