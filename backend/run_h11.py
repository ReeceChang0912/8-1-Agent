import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
# .env 由 backend/main.py 自行加载

import uvicorn
uvicorn.run(
    "backend.main:app",
    host="0.0.0.0",
    port=8000,
    workers=1,
    http="h11",       # 不使用 httptools（Python 3.14 兼容）
    loop="asyncio",   # 不使用 uvloop（Windows 兼容）
    log_level="info"
)
