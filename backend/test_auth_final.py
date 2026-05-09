import http.client, json
c = http.client.HTTPConnection("localhost", 8000, timeout=10)
body = json.dumps({"family_id": "807325", "member_name": "我"})
c.request("POST", "/api/auth/login", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = r.read()
print(f"login: {r.status}")
print(d.decode(errors='replace')[:200])
c.close()
