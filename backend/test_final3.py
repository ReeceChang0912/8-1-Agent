import http.client, json
c = http.client.HTTPConnection("localhost", 8000, timeout=10)

# Test login with existing family
body = json.dumps({"family_id": "807325", "member_name": "我"})
c.request("POST", "/api/auth/login", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = r.read()
print(f"Login: {r.status}")
j = json.loads(d.decode('utf-8'))
if r.status == 200:
    print(f"  success: {j.get('success')}")
    print(f"  message: {j.get('message', '')[:50]}")
    if j.get('success'):
        print(f"  session: {j.get('session_id','')[:20]}...")
else:
    print(f"  {d.decode('utf-8','replace')[:100]}")

c.close()
