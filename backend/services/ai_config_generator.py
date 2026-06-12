"""
AI 配置生成器 - 接入第三方 LLM API，为签到助手生成 api_config JSON 配置。
"""

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
        # 自动补全 /v1 路径
        base_url = api_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = base_url + '/v1'

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
        # 自动补全 /v1 路径
        base_url = api_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = base_url + '/v1'

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
