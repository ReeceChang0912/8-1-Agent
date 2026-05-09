import psycopg2

# 试试 main.py 里硬编码的连接串
passwords = {
    "postgres:piMmXrF7exas4FBm": ("postgres", "piMmXrF7exas4FBm"),
    "postgres:LFDDWHpyphWxxs7Z": ("postgres", "LFDDWHpyphWxxs7Z"),
    "admin:LFDDWHpyphWxxs7Z": ("admin", "LFDDWHpyphWxxs7Z"),
    "admin:piMmXrF7exas4FBm": ("admin", "piMmXrF7exas4FBm"),
}

for label, (user, pw) in passwords.items():
    try:
        conn = psycopg2.connect(host="47.86.227.185", port=5432, user=user, password=pw, dbname="agent", connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT current_user, version()")
        row = cur.fetchone()
        print(f"  {label}: OK - {row[0]}")
        conn.close()
    except Exception as e:
        print(f"  {label}: FAIL - {str(e)[:60]}")
