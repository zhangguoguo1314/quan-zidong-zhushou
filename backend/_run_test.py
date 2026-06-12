import sys, subprocess, time, json, urllib.request
BASE = "http://127.0.0.1:8000"
def http(method, path, data=None, token=None):
    req = urllib.request.Request(BASE + path, method=method)
    if token: req.add_header("Authorization", "Bearer " + token)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json"); req.data = body
    else: req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8"); return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return e.code, json.loads(body) if body else {}

print("HEALTH:", http("GET", "/api/health"))
status, _ = http("POST", "/api/auth/register", {"email": "user@test.com", "password": "password123"})
status, d = http("POST", "/api/auth/login", {"email": "user@test.com", "password": "password123"})
token = d["access_token"]; print("LOGIN OK, token len", len(token))

# --- category CRUD ---
s, _ = http("POST", "/api/sites/categories", {"name": "资源下载", "display_name": "资源下载类站点", "icon": "📦", "color": "#409EFF"}, token=token); print("CREATE cat:", s)
s, _ = http("POST", "/api/sites/categories", {"name": "AI工具", "display_name": "AI工具类网站", "icon": "🤖", "color": "#67C23A", "sort_order": 1}, token=token); print("CREATE cat2:", s)
s, cats = http("GET", "/api/sites/categories", token=token); print("LIST cats:", s, len(cats))
s, _ = http("PUT", "/api/sites/categories/1", {"display_name": "资源下载（已更新）"}, token=token); print("UPDATE cat:", s)
s, _ = http("DELETE", "/api/sites/categories/2", token=token); print("DELETE cat2:", s)
s, cats = http("GET", "/api/sites/categories", token=token); print("LIST after delete:", len(cats))

# --- site CRUD with category ---
s, _ = http("POST", "/api/sites", {"name": "TestSite", "type": "custom-api", "category": "资源下载"}, token=token); print("CREATE site:", s)
s, sites = http("GET", "/api/sites", token=token); print("LIST sites:", s, len(sites))
s, g = http("GET", "/api/sites/grouped", token=token); print("GROUPED:", s, list(g.keys()))

# --- message template preview ---
s, p = http("POST", "/api/settings/templates/preview", {"template": "签到成功 - {account_name} @ {site_name} ({time})", "scenario": "success"}, token=token); print("TPL preview:", s, "rendered:", p.get("rendered","")[:60])

# --- wechat bot test ---
s, botres = http("POST", "/api/settings/test-wechat-bot", {"webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=626539fe-eca7-447e-9367-a89f88f6f13d"}, token=token); print("BOT test:", s, botres)

print("\n=== ALL TESTS DONE ===")
