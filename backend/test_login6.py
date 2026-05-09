import sys, os, json, http.client

# Test GET first (known to work)
c = http.client.HTTPConnection("localhost", 8000, timeout=10)
c.request("GET", "/api/auth/verify?session_id=test")
r = c.getresponse()
d = r.read()
print(f"GET /verify: {r.status} - {d[:80]}")

# Test POST with simple handler - just try root path
body = json.dumps({"family_id": "1", "member_name": "test"})
c.request("POST", "/api/auth/login", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = r.read()
print(f"POST /login: {r.status}")
print(f"Headers: {dict(r.getheaders())}")
print(f"Body bytes: {len(d)}")
print(f"Body: {d[:200]}")
c.close()
