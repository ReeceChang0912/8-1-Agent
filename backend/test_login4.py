import http.client, json
conn = http.client.HTTPConnection("localhost", 8000, timeout=10)
headers = {"Content-Type": "application/json"}

# Test login
body = json.dumps({"family_id": "807325", "member_name": "我"})
conn.request("POST", "/api/auth/login", body, headers)
resp = conn.getresponse()
data = resp.read().decode()
print(f"Login: {resp.status} - {resp.reason}")
print(f"Body: {data[:300]}")

# Test create-family
body2 = json.dumps({"family_name": "家庭B", "admin_name": "小明"})
conn.request("POST", "/api/auth/create-family", body2, headers)
resp2 = conn.getresponse()
data2 = resp2.read().decode()
print(f"\nCreate: {resp2.status} - {resp2.reason}")
print(f"Body: {data2[:300]}")
conn.close()
