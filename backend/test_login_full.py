import http.client, json
c = http.client.HTTPConnection("localhost", 8000, timeout=10)

# 用刚创建的家庭登录
body = json.dumps({"family_id": "589126", "member_name": "测试"})
c.request("POST", "/api/auth/login", body, {"Content-Type": "application/json"})
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print(f"Login: {r.status}")
for k, v in d.items():
    if k == 'session_id':
        print(f"  {k}: {str(v)[:30]}...")
    else:
        print(f"  {k}: {str(v)[:60]}")

# 测试 stats
c.request("GET", "/api/stats")
r = c.getresponse()
d = json.loads(r.read().decode('utf-8'))
print(f"\nStats: {r.status} -> members={d.get('members_count',0)}, reminders={d.get('reminders_count',0)}")

c.close()
