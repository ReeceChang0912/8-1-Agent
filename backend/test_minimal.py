"""
Minimal FastAPI test - no routers, just a POST endpoint
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.post("/test")
def test_post(data: dict):
    return {"received": data}

@app.get("/test")
def test_get():
    return {"hello": "world"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
