import sys, os
sys.path.insert(0, '.'); sys.path.insert(0, '..')
os.chdir('..')
os.environ['DATABASE_URL'] = 'postgresql://postgres:piMmXrF7exas4FBm@47.86.227.185:5432/agent'
import psycopg2
from psycopg2.extras import RealDictCursor
conn = psycopg2.connect(os.environ['DATABASE_URL'], cursor_factory=RealDictCursor)
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS families (
        family_id TEXT PRIMARY KEY,
        family_name TEXT NOT NULL,
        members TEXT DEFAULT '[]',
        settings TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        member_name TEXT NOT NULL,
        login_time TEXT,
        expires_at TEXT,
        is_active BOOLEAN DEFAULT TRUE
    )
""")
cur.execute("""INSERT INTO families (family_id, family_name, members) 
    VALUES ('807325', '可爱一家', '["我","鲨鱼"]')
    ON CONFLICT (family_id) DO NOTHING""")
cur.execute("SELECT * FROM families")
print("families:", [dict(r) for r in cur.fetchall()])
cur.close(); conn.close()
print("setup OK")
