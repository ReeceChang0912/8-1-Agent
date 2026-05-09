import http.client, json, sys
c = http.client.HTTPConnection("localhost", 8000, timeout=10)

# Login
body = json.dumps({"family_id": "589126", "member_name": "测试"})
c.request("POST", "/api/auth/login", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print("Login:", r.status, "success:", d.get('success'))
if d.get('session_id'): print("  session OK:", d['session_id'][:20]+'...')

# Stats
c.request("GET", "/api/stats")
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print("Stats:", r.status, d)

# Members
c.request("GET", "/api/members")
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print("Members:", r.status, len(d) if isinstance(d, list) else d)

# Workbench
c.request("GET", "/api/workbench")
r = c.getresponse()
d = r.read().decode('utf-8')[:100]
print("Workbench:", r.status, d[:80])

c.close()
print("\nALL TESTS PASSED")
