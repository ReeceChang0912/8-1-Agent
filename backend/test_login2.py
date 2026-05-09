import urllib.request, json
url = "http://localhost:8000/api/auth/login"
data = json.dumps({"family_id": "807325", "member_name": "我"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print("OK", resp.status, resp.read().decode()[:300])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}")
    body = e.read()
    print("Body:", body.decode()[:300])
except Exception as e:
    print(f"ERR {type(e).__name__}: {str(e)[:200]}")
