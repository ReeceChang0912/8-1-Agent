import urllib.request, json
url = "http://localhost:8000/api/auth/login"
data = json.dumps({"family_id": "807325", "member_name": "我"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print("OK:", resp.status, resp.read().decode()[:500])
except urllib.error.HTTPError as e:
    body = e.read().decode()[:500]
    print(f"ERROR {e.code}: {body}")
