import http.client, json
c = http.client.HTTPConnection("localhost", 8000, timeout=10)

# 1. Create family
body = json.dumps({"family_name": "测试家庭", "admin_name": "测试"})
c.request("POST", "/api/auth/create-family", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print(f"Create family: {r.status}")
for k,v in d.items():
    print(f"  {k}: {str(v)[:60]}")

c.close()
