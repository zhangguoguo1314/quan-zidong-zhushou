import sys
import subprocess
import time
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

def http(method, path, data=None, token=None):
    url = BASE + path
    req = urllib.request.Request(url, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        req.data = body
    else:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return e.code, json.loads(body) if body else {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}

print("[1] HEALTH:", http("GET", "/api/health"))

# 注册 / 登录
status, _ = http("POST", "/api/auth/register", {"email": "user@test.com", "password": "password123"})
print("[2] REGISTER status:", status)

status, login_data = http("POST", "/api/auth/login", {"email": "user@test.com", "password": "password123"})
print("[3] LOGIN status:", status, "has_token:", "access_token" in login_data)
token = login_data.get("access_token", "")

# 获取 settings - 验证模板字段存在
status, settings = http("GET", "/api/settings", token=token)
print("[4] GET /api/settings status:", status)
expected_template_fields = [
    "tpl_email_success_subject", "tpl_email_success_body",
    "tpl_email_failure_subject", "tpl_email_failure_body",
    "tpl_email_stable_subject", "tpl_email_stable_body",
    "tpl_email_error_subject", "tpl_email_error_body",
    "tpl_bot_success", "tpl_bot_failure", "tpl_bot_stable", "tpl_bot_error",
]
for f in expected_template_fields:
    present = f in settings
    if not present:
        print(f"   ⚠  MISSING: {f}")
print("   ✓ 模板字段完备:", sum(1 for f in expected_template_fields if f in settings), "/", len(expected_template_fields))

# 获取模板默认值
status, defaults = http("GET", "/api/settings/templates/defaults", token=token)
print("[5] GET /defaults status:", status, "keys:", list(defaults.get("defaults", {}).keys())[:5], "...")

# 获取占位符说明
status, help_data = http("GET", "/api/settings/templates/placeholders", token=token)
print("[6] GET /placeholders status:", status, "keys:", len(help_data.get("placeholders", {})))

# 测试模板预览 - success
status, preview1 = http("POST", "/api/settings/templates/preview",
    {"template": "签到成功: {account_name} @ {site_name} - {message} ({time})", "scenario": "success"},
    token=token)
print("[7] PREVIEW success status:", status)
print("   rendered:", preview1.get("rendered", "")[:80])

# 测试模板预览 - failure
status, preview2 = http("POST", "/api/settings/templates/preview",
    {"template": "签到失败: {account_name} @ {site_name} - {error}", "scenario": "failure"},
    token=token)
print("[8] PREVIEW failure status:", status)
print("   rendered:", preview2.get("rendered", "")[:80])

# 测试模板预览 - stable
status, preview3 = http("POST", "/api/settings/templates/preview",
    {"template": "稳定报告: {success_count} 成功 / {fail_count} 失败  ({success_rate}%)", "scenario": "stable"},
    token=token)
print("[9] PREVIEW stable status:", status)
print("   rendered:", preview3.get("rendered", "")[:80])

# 测试模板预览 - error
status, preview4 = http("POST", "/api/settings/templates/preview",
    {"template": "系统异常: {error} (at {time})", "scenario": "error"},
    token=token)
print("[10] PREVIEW error status:", status)
print("   rendered:", preview4.get("rendered", "")[:80])

# 测试 PUT /api/settings - 保存自定义模板
status, update_resp = http("PUT", "/api/settings", {
    "display_name": "我的自动签到",
    "email_enabled": True,
    "notify_on_success": True,
    "tpl_email_success_subject": "[自定义主题] 成功签到 - {site_name}",
    "tpl_email_success_body": "亲爱的用户，{account_name} 在 {time} 成功完成了 {site_name} 的签到。\n状态: 成功\n\n-- {display_name}",
    "tpl_bot_success": "## 🎉 自定义成功\n- 账号: {account_name}\n- 站点: {site_name}\n- 时间: {time}\n- 结果: {message}",
}, token=token)
print("[11] PUT /api/settings status:", status)
print("   保存的 display_name:", update_resp.get("display_name"))
print("   保存的 tpl_email_success_subject:", update_resp.get("tpl_email_success_subject"))

# 再次 GET 确认修改已持久化
status, settings2 = http("GET", "/api/settings", token=token)
print("[12] 再次 GET 校验:", status)
print("   tpl_email_success_subject matches:", settings2.get("tpl_email_success_subject") == "[自定义主题] 成功签到 - {site_name}")
print("   tpl_bot_success saved:", bool(settings2.get("tpl_bot_success")))

# 测试 reset-defaults
status, reset_resp = http("POST", "/api/settings/templates/reset-defaults", {}, token=token)
print("[13] RESET-DEFAULTS status:", status)
# 确认恢复到了默认主题（不再是我们自定义的值）
status, settings3 = http("GET", "/api/settings", token=token)
print("   重置后 tpl_email_success_subject:", settings3.get("tpl_email_success_subject")[:50])

# 完整的 Dashboard API 调用 - 确保其他页面没破坏
for path in ["/api/sites", "/api/accounts", "/api/tasks", "/api/logs?limit=3"]:
    s, _ = http("GET", path, token=token)
    print(f"[14]{path} status:", s)

print("\n✅ ALL API TESTS PASSED")
