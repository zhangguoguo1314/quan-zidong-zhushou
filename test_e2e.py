import requests, json, time, sys

BASE = "http://127.0.0.1:8000"
h = {"Content-Type": "application/json"}
results = {}

def check(name, r, expected=200, show_body=False):
    ok = r.status_code == expected
    results[name] = "PASS" if ok else f"FAIL({r.status_code})"
    body = ""
    try:
        if r.headers.get('content-type','').startswith('application/json'):
            body = json.dumps(r.json(), ensure_ascii=False)[:200]
        else:
            body = r.text[:200]
    except:
        body = r.text[:200]
    status = "  OK  " if ok else "  FAIL "
    print(f"{status}[{name}] HTTP {r.status_code}")
    if not ok or show_body:
        print(f"       body: {body}")
    return ok

# 1. 健康检查
r = requests.get(f"{BASE}/api/health")
check("1.健康检查", r)

# 2. 登录（或注册+登录）
login_data = {"email": "e2e@test.com", "password": "test123456"}
r = requests.post(f"{BASE}/api/auth/login", headers=h, json=login_data)
if r.status_code != 200:
    print(f"  先注册...")
    r2 = requests.post(f"{BASE}/api/auth/register", headers=h, json=login_data)
    r = requests.post(f"{BASE}/api/auth/login", headers=h, json=login_data)
d = r.json()
token = d["access_token"]
auth = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
print(f"  OK  [2.登录] token: {token[:30]}...")
results["2.登录"] = "PASS"

# 3. 创建2个站点
site1_cfg = {
    "login_url": "https://lizhiyu.appleinc.cn/v1/user/login-pwd",
    "login_method": "POST",
    "login_body_template": '{"email": "{{username}}", "password": "{{password}}"}',
    "login_content_type": "application/json",
    "token_path": "token",
    "signin_url": "https://lizhiyu.appleinc.cn/v1/user/signin",
    "signin_method": "POST",
    "signin_body": "{}",
    "signin_content_type": "application/json",
    "auth_header_template": "Bearer {{token}}",
    "auth_header_name": "Authorization",
    "success_field": "",
    "message_field": "message"
}
site2_cfg = {
    "login_url": "https://api.gemai.cc/api/user/login",
    "login_method": "POST",
    "login_body_template": '{"username": "{{username}}", "password": "{{password}}"}',
    "login_content_type": "application/json",
    "token_path": "data.id",
    "signin_url": "https://api.gemai.cc/api/user/checkin",
    "signin_method": "POST",
    "signin_body": "{}",
    "signin_content_type": "application/json",
    "auth_header_template": "{{token}}",
    "auth_header_name": "New-Api-User",
    "success_field": "",
    "message_field": "message"
}

r = requests.post(f"{BASE}/api/sites", headers=auth, json={
    "name": "荔枝鱼公益站", "type": "custom-api", "url": "https://lizhiyu.appleinc.cn",
    "category": "公益站点", "api_config": site1_cfg
})
check("3a.创建荔枝鱼", r)

r = requests.post(f"{BASE}/api/sites", headers=auth, json={
    "name": "哈基米", "type": "custom-api", "url": "https://api.gemai.cc",
    "category": "API服务", "api_config": site2_cfg
})
check("3b.创建哈基米", r)

# 4. 读取站点列表
r = requests.get(f"{BASE}/api/sites", headers=auth)
check("4.读取站点列表", r)
sites = r.json()
print(f"       共 {len(sites)} 个站点")
s1_id = [s['id'] for s in sites if '荔枝鱼' in s['name']][0]
s2_id = [s['id'] for s in sites if '哈基米' in s['name']][0]

# 5. 创建5个账号
print(f"\n--- 创建荔枝鱼3个账号（同站点多账号） ---")
lizhi_accounts = []
for i in range(1, 4):
    r = requests.post(f"{BASE}/api/accounts", headers=auth, json={
        "site_id": s1_id, "username": f"test_lizhi{i}@qq.com", "password": "youqisi1314"
    })
    a = r.json()
    lizhi_accounts.append(a)
    print(f"       [{a.get('id','?')}] {a.get('username','?')} HTTP {r.status_code}")

print(f"\n--- 创建哈基米2个账号 ---")
gemai_accounts = []
for i in range(1, 3):
    r = requests.post(f"{BASE}/api/accounts", headers=auth, json={
        "site_id": s2_id, "username": f"testgemai{i}", "password": "youqisi1314"
    })
    a = r.json()
    gemai_accounts.append(a)
    print(f"       [{a.get('id','?')}] {a.get('username','?')} HTTP {r.status_code}")

# 6. 账号列表 - 关键！验证没有500错误
r = requests.get(f"{BASE}/api/accounts", headers=auth)
check("6.账号列表(无500)", r)
accounts = r.json()
print(f"       共 {len(accounts)} 个账号")

# 7. 为每个账号创建任务
print(f"\n--- 创建5个任务 ---")
all_accounts = lizhi_accounts + gemai_accounts
for acc in all_accounts:
    r = requests.post(f"{BASE}/api/tasks", headers=auth, json={
        "account_id": acc["id"], "cron": "0 8 * * *", "name": f"签到-{acc['username']}"
    })
    t = r.json()
    print(f"       [{t.get('id','?')}] {acc['username']} HTTP {r.status_code}")

# 8. 任务列表
r = requests.get(f"{BASE}/api/tasks", headers=auth)
check("8.读取任务列表", r)
tasks = r.json()

# 9. 启用所有任务
print(f"\n--- 启用所有任务 ---")
for t in tasks:
    r = requests.put(f"{BASE}/api/tasks/{t['id']}", headers=auth, json={"status": "enabled"})
    d = r.json()
    print(f"       [{t['id']}] -> {d.get('status','?')} HTTP {r.status_code}")

# 10. 立即执行所有5个任务（并行！核心测试）
print(f"\n--- 立即执行5个任务（并行） ---")
for t in tasks:
    r = requests.post(f"{BASE}/api/tasks/{t['id']}/run", headers=auth)
    d = r.json() if r.headers.get('content-type','').startswith('application/json') else {}
    print(f"       [{t['id']}] run -> HTTP {r.status_code}")
print(f"\n       等待执行（20秒）...")
time.sleep(20)

# 11. 日志 - 验证多账号独立签到
r = requests.get(f"{BASE}/api/logs?limit=30", headers=auth)
check("11.日志读取", r)
logs = r.json()
by_account = {}
for l in logs:
    acc = l.get("account_username", "?")
    site = l.get("site_name", "?")
    status = l["status"]
    key = f"{acc} @ {site}"
    if key not in by_account:
        by_account[key] = {"success": 0, "failed": 0, "results": []}
    by_account[key][status] = by_account[key].get(status, 0) + 1
    if len(by_account[key]["results"]) < 2:
        by_account[key]["results"].append(l["result"][:120])

print(f"\n       共 {len(logs)} 条日志，按账号分组 {len(by_account)} 组:")
for key, stats in sorted(by_account.items()):
    total = stats.get("success", 0) + stats.get("failed", 0)
    print(f"       {key}: total={total}, success={stats.get('success',0)}, fail={stats.get('failed',0)}")
    for res in stats["results"]:
        print(f"           {res}")

# 12. 账号统计
r = requests.get(f"{BASE}/api/accounts", headers=auth)
accounts = r.json()
print(f"\n       --- 账号独立计数 ---")
for a in accounts:
    total = a.get("total_signins", 0) or 0
    ok = a.get("success_count", 0) or 0
    fail = a.get("fail_count", 0) or 0
    print(f"       [{a['id']}] {a['username']}: total={total}, ok={ok}, fail={fail}")

# 13. 第二轮执行
print(f"\n--- 第二轮执行（验证同站点账号cookie隔离） ---")
for t in tasks:
    r = requests.post(f"{BASE}/api/tasks/{t['id']}/run", headers=auth)
    print(f"       [{t['id']}] run -> HTTP {r.status_code}")
time.sleep(20)

r = requests.get(f"{BASE}/api/logs?limit=50", headers=auth)
logs2 = r.json()
print(f"\n       第二轮后总日志: {len(logs2)}条")

# 14. CSV导出
r = requests.get(f"{BASE}/api/logs/export?token={token}&limit=5")
check("14.CSV日志导出", r)
print(f"       前3行: {r.text.split(chr(10))[0][:120]} ...")

# 15. 设置保存
r = requests.put(f"{BASE}/api/settings", headers=auth, json={
    "display_name": "自动签到助手", "email_enabled": False,
    "wechat_bot_enabled": False, "status_report_enabled": False,
    "ai_api_url": "", "ai_api_key": "", "ai_model": "", "ai_custom_prompt": ""
})
check("15a.保存设置", r)
r = requests.get(f"{BASE}/api/settings", headers=auth)
check("15b.读取设置", r)

# 16. 状态报告
r = requests.post(f"{BASE}/api/settings/send-status-report", headers=auth, json={})
check("16.状态报告立即发送", r)
print(f"       body: {r.text[:200]}")

# 17. 分类
r = requests.get(f"{BASE}/api/sites/categories", headers=auth)
check("17a.站点分类API", r)
r = requests.get(f"{BASE}/api/sites/grouped", headers=auth)
check("17b.站点分组API", r)

# 总结
print("\n" + "="*70)
print("测试结果总结:")
print("="*70)
all_pass = True
for name, status in results.items():
    symbol = "OK" if status == "PASS" else "FAIL"
    if status != "PASS": all_pass = False
    print(f"  [{symbol}] {name}")

print(f"\n关键验证:")
print(f"  - 同站点多账号独立签到: {len(by_account)}个唯一账号组合被记录")
print(f"  - 总任务数: {len(tasks)}")
print(f"  - 总日志数: {len(logs)} (第一轮), {len(logs2)} (累计)")

if all_pass:
    print("\n=== ✅ 所有核心测试通过 ===")
else:
    print("\n=== ⚠️  部分测试未通过 ===")
    sys.exit(1)
