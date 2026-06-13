import httpx
import json
import re
from typing import Optional

DEFAULT_PROMPT = """你是一个 API 抓包分析助手。请只分析用户拥有或授权测试的网站。

目标：为"全自动签到助手"生成 api_config JSON 配置。

用户会提供：网站地址、测试账号、测试密码，以及 F12 Network 截图或 HAR 文件内容。

请你完成：
1. 分析登录流程：找到登录接口 URL、请求方法、Content-Type、请求体格式、账号/密码字段名
2. 分析签到流程：找到签到接口 URL、请求方法、认证方式（Bearer Token / Cookie / 自定义Header）
3. 判断"今日已签到"是否算成功

输出格式：只输出 JSON，不要多余解释：
{
  "login_url": "完整登录接口地址",
  "login_method": "POST",
  "login_body_template": "{\\"username\\": \\"{{username}}\\", \\"password\\": \\"{{password}}\\"}",
  "login_content_type": "application/json",
  "token_path": "token",
  "signin_url": "完整签到接口地址",
  "signin_method": "POST",
  "signin_body": "{}",
  "signin_content_type": "application/json",
  "auth_header_name": "Authorization",
  "auth_header_template": "Bearer {{token}}",
  "success_field": "success",
  "message_field": "message"
}

如果依赖 Cookie 而非 Token，auth_header_name 和 auth_header_template 留空，额外添加 "use_login_cookies": true。"""


async def fetch_models(api_url: str, api_key: str) -> list:
    """拉取 API 下的模型列表"""
    try:
        # 清理 URL：去掉 /console 等前端路径，保留 /v1
        base_url = api_url.rstrip('/')
        # 去掉常见的前端路径
        for prefix in ['/console', '/admin', '/dashboard', '/app']:
            if base_url.endswith(prefix):
                base_url = base_url[:-len(prefix)]
                break
        # 确保有 /v1
        if not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'

        async with httpx.AsyncClient(timeout=15, verify=False, follow_redirects=True) as client:
            resp = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if resp.status_code != 200:
                raise Exception(f"API 返回 HTTP {resp.status_code}: {resp.text[:200]}")

            try:
                data = resp.json()
            except Exception:
                raise Exception(f"API 返回非 JSON 响应: {resp.text[:200]}。请确认 API 地址正确（通常以 /v1 结尾，如 https://xxx.com/v1）")

            models = []
            if "data" in data and isinstance(data["data"], list):
                for m in data["data"]:
                    if isinstance(m, dict) and "id" in m:
                        models.append(m["id"])
                    elif isinstance(m, str):
                        models.append(m)
            elif isinstance(data, list):
                models = [m["id"] if isinstance(m, dict) and "id" in m else str(m) for m in data]

            if not models:
                raise Exception("API 返回的模型列表为空，请检查 API Key 是否正确")

            return sorted(models)
    except httpx.TimeoutException:
        raise Exception("请求超时，请检查 API 地址是否可访问")
    except httpx.ConnectError:
        raise Exception("无法连接到 API 地址，请检查地址是否正确")
    except Exception as e:
        if "拉取模型列表失败" in str(e) or "API 返回" in str(e) or "请求超时" in str(e) or "无法连接" in str(e):
            raise
        raise Exception(f"拉取模型列表失败: {str(e)}")


async def generate_config(
    api_url: str,
    api_key: str,
    model: str,
    user_input: str,
    custom_prompt: str = ""
) -> dict:
    """调用 LLM 生成 api_config"""
    prompt = custom_prompt.strip() if custom_prompt.strip() else DEFAULT_PROMPT
    full_prompt = f"{prompt}\n\n用户提供的以下信息：\n{user_input}"

    try:
        # 清理 URL：去掉 /console 等前端路径，保留 /v1
        base_url = api_url.rstrip('/')
        for prefix in ['/console', '/admin', '/dashboard', '/app']:
            if base_url.endswith(prefix):
                base_url = base_url[:-len(prefix)]
                break
        if not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'

        async with httpx.AsyncClient(timeout=60, verify=False, follow_redirects=True) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个API分析助手，只输出JSON格式结果。"},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            resp.raise_for_status()
            data = resp.json()

            # 检查 API 错误响应
            if "error" in data:
                return {"success": False, "error": data["error"].get("message", str(data["error"]))}

            content = data["choices"][0]["message"]["content"]

            # 尝试从响应中提取 JSON
            # 可能在 ```json ... ``` 代码块中
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content

            # 找到第一个 { 和最后一个 }
            start = json_str.find('{')
            end = json_str.rfind('}')
            if start >= 0 and end > start:
                json_str = json_str[start:end + 1]

            config = json.loads(json_str)
            return {"success": True, "config": config, "raw_response": content}

    except httpx.TimeoutException:
        return {"success": False, "error": "AI 请求超时，请检查 API 地址是否可达"}
    except httpx.ConnectError:
        return {"success": False, "error": "AI 连接失败，请检查 API 地址是否正确"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"AI 返回的内容无法解析为 JSON: {str(e)}"}
    except KeyError as e:
        return {"success": False, "error": f"AI 响应格式异常，缺少字段: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"AI 生成配置失败: {str(e)}"}


# ============ HAR 文件解析与精简 ============

# 登录/签到相关的关键词，用于从海量 HAR 条目中筛选
_SIGNIN_KEYWORDS = [
    "login", "signin", "sign-in", "sign_in", "checkin", "check-in", "check_in",
    "sign", "auth", "token", "session", "cookie",
    "login-pwd", "logging", "misign", "qiandao",
    "user/login", "user/sign", "user/check",
]

# 需要排除的噪声请求（静态资源等）
_EXCLUDE_EXTENSIONS = [
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
    ".woff2", ".ttf", ".eot", ".map", ".webp", ".mp4", ".mp3", ".webm",
    ".pdf", ".zip", ".gz", ".tar",
]

_EXCLUDE_CONTENT_TYPES = [
    "image/", "font/", "audio/", "video/", "application/pdf",
    "application/zip", "application/octet-stream",
]


def parse_and_simplify_har(har_content: str) -> dict:
    """
    解析 HAR 文件，自动精简为只包含登录/签到相关的请求。

    返回:
    {
        "success": bool,
        "total_entries": int,        # HAR 总请求数
        "filtered_entries": int,     # 筛选后的请求数
        "simplified_text": str,      # 精简后的文本，可直接发给 AI
        "entries": list,              # 筛选后的请求详情列表
        "error": str,                 # 错误信息
    }
    """
    try:
        har = json.loads(har_content)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"HAR 文件 JSON 解析失败: {str(e)}"}

    entries = har.get("log", {}).get("entries", [])
    total = len(entries)

    if total == 0:
        return {"success": False, "error": "HAR 文件中没有请求记录", "total_entries": 0}

    # 筛选相关请求
    filtered = []
    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        method = entry.get("request", {}).get("method", "")
        status = entry.get("response", {}).get("status", 0)
        resp_content_type = ""

        # 检查响应 Content-Type
        resp_headers = entry.get("response", {}).get("headers", [])
        for h in resp_headers:
            if h.get("name", "").lower() == "content-type":
                resp_content_type = h.get("value", "")
                break

        # 排除静态资源
        url_lower = url.lower()
        if any(url_lower.endswith(ext) for ext in _EXCLUDE_EXTENSIONS):
            continue
        if any(ct in resp_content_type.lower() for ct in _EXCLUDE_CONTENT_TYPES):
            continue

        # 排除 OPTIONS 预检请求
        if method == "OPTIONS":
            continue

        # 关键词匹配
        url_path = url.split("?")[0].lower()
        matched = False
        for kw in _SIGNIN_KEYWORDS:
            if kw.lower() in url_path:
                matched = True
                break

        # 也检查 POST 请求（登录和签到通常是 POST）
        if not matched and method == "POST":
            # 检查请求体是否包含密码/用户名字段
            post_data = entry.get("request", {}).get("postData", {})
            mime_type = post_data.get("mimeType", "")
            text = post_data.get("text", "")
            if text and ("password" in text.lower() or "username" in text.lower() or "email" in text.lower()):
                matched = True

        if matched:
            filtered.append(entry)

    if not filtered:
        return {
            "success": False,
            "error": f"未找到登录/签到相关的请求。HAR 共 {total} 个请求，但都不匹配登录/签到关键词。",
            "total_entries": total,
            "filtered_entries": 0,
        }

    # 精简每个条目，只保留关键信息
    simplified_entries = []
    for entry in filtered:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        req_headers = {h["name"]: h["value"] for h in req.get("headers", [])}
        resp_headers_list = resp.get("headers", [])

        # 提取 Set-Cookie（登录响应的关键信息）
        set_cookies = []
        for h in resp_headers_list:
            if h.get("name", "").lower() == "set-cookie":
                set_cookies.append(h["value"])

        simplified = {
            "url": req.get("url", ""),
            "method": req.get("method", ""),
            "status": resp.get("status", 0),
            "request_headers": {k: v for k, v in req_headers.items()
                               if k.lower() in ["content-type", "authorization", "cookie", "referer", "origin"]},
            "request_body": req.get("postData", {}).get("text", ""),
            "response_content_type": "",
            "response_body_preview": "",
            "set_cookies": set_cookies,
        }

        # 提取响应 Content-Type
        for h in resp_headers_list:
            if h.get("name", "").lower() == "content-type":
                simplified["response_content_type"] = h["value"]
                break

        # 提取响应体预览（截断到 2000 字符）
        resp_content = resp.get("content", {})
        resp_text = resp_content.get("text", "")
        if resp_text:
            # 如果是 base64 编码的，尝试解码
            encoding = resp_content.get("encoding", "")
            if encoding == "base64":
                try:
                    import base64
                    resp_text = base64.b64decode(resp_text).decode("utf-8", errors="replace")
                except Exception:
                    resp_text = "(base64 encoded, 无法解码)"
            simplified["response_body_preview"] = resp_text[:2000]

        simplified_entries.append(simplified)

    # 生成精简文本（可直接发给 AI）
    text_parts = [
        f"=== HAR 文件分析结果（共 {total} 个请求，筛选出 {len(filtered)} 个相关请求） ===\n"
    ]

    for i, entry in enumerate(simplified_entries, 1):
        text_parts.append(f"--- 请求 {i} ---")
        text_parts.append(f"URL: {entry['method']} {entry['url']}")
        text_parts.append(f"状态码: {entry['status']}")
        if entry["request_headers"]:
            text_parts.append(f"请求头: {json.dumps(entry['request_headers'], ensure_ascii=False)}")
        if entry["request_body"]:
            text_parts.append(f"请求体: {entry['request_body'][:1000]}")
        if entry["response_content_type"]:
            text_parts.append(f"响应类型: {entry['response_content_type']}")
        if entry["response_body_preview"]:
            text_parts.append(f"响应体: {entry['response_body_preview'][:1000]}")
        if entry["set_cookies"]:
            # 只保留 cookie 名称，隐藏值
            cookie_names = []
            for c in entry["set_cookies"]:
                name = c.split("=")[0].strip()
                cookie_names.append(name)
            text_parts.append(f"Set-Cookie: {', '.join(cookie_names)}")
        text_parts.append("")

    simplified_text = "\n".join(text_parts)

    return {
        "success": True,
        "total_entries": total,
        "filtered_entries": len(filtered),
        "simplified_text": simplified_text,
        "entries": simplified_entries,
    }
