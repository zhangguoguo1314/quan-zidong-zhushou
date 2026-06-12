# 三站点签到API测试报告

## 站点1: 哈基米API站 (api.gemai.cc)

### 平台类型
New API (one-api) 平台

### 1. 登录接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://api.gemai.cc/api/user/login` |
| **方法** | POST |
| **Content-Type** | application/json |
| **请求体** | `{"username":"2898263796@qq.com","password":"youqisi1314"}` |

**登录响应:**
```json
{
  "data": {
    "display_name": "heyeyyds",
    "group": "default",
    "id": 37447,
    "role": 1,
    "status": 1,
    "username": "heyeyyds"
  },
  "message": "",
  "success": true
}
```

**认证方式:**
- 登录成功后，服务器返回 `Set-Cookie: session=<base64_encoded_session>` (HttpOnly, SameSite=Strict)
- 后续请求需要携带此 session cookie
- 同时需要添加请求头 `New-Api-User: <用户ID>` (即 `data.id` 的值，本例为 `37447`)

### 2. 签到接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://api.gemai.cc/api/user/checkin` |
| **方法** | POST |
| **Content-Type** | 无需 (无请求体) |
| **请求头** | `Cookie: session=<session_value>` + `New-Api-User: 37447` |
| **请求体** | 无 |

**签到成功响应:**
```json
{"message": "签到成功，获得额度 $0.01", "success": true}
```

**签到失败响应 (已签到):**
```json
{"message": "今日已签到", "success": false}
```

### 3. 成功/失败判断
- **成功**: `"success": true`
- **失败**: `"success": false`，`message` 字段包含原因（如 "今日已签到"）

### 完整 curl 示例
```bash
# 登录
curl -s -c /tmp/gemai_cookie -X POST "https://api.gemai.cc/api/user/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"2898263796@qq.com","password":"youqisi1314"}'

# 签到 (user_id 从登录响应的 data.id 获取)
curl -s -b /tmp/gemai_cookie -X POST "https://api.gemai.cc/api/user/checkin" \
  -H "New-Api-User: 37447"
```

---

## 站点2: 荔枝鱼 / 辉哥boy公益中转站 (lizhiyu.appleinc.cn)

### 平台类型
Vue 3 前端 + 自定义后端 API (类似 New API 架构)

### 1. 登录接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://lizhiyu.appleinc.cn/v1/user/login-pwd` |
| **方法** | POST |
| **Content-Type** | application/json; charset=utf-8 |
| **请求体** | `{"email":"2898263796@qq.com","password":"youqisi1314"}` |

**注意:** 请求体字段名是 `email`（不是 `username`）。

**登录响应:**
```json
{
  "message": "Login successful",
  "token": "0f9cbecc1e8b7ab5644994efa0f51ca8",
  "email": "2898263796@qq.com",
  "nickname": "heye"
}
```

**认证方式:**
- 登录成功后返回 `token` 字符串
- 后续请求通过 `Authorization: Bearer <token>` 请求头认证
- 前端将 token 存储在 localStorage (key: `huige_user`)

### 2. 签到接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://lizhiyu.appleinc.cn/v1/user/signin` |
| **方法** | POST |
| **Content-Type** | application/json; charset=utf-8 |
| **请求头** | `Authorization: Bearer <token>` |
| **请求体** | `{}` (空对象) |

**签到成功响应 (推测):**
```json
{"reward": 0.01, "balance": 1.23}
```

**签到失败响应 (已签到):**
```json
{
  "error": {
    "message": "You have already signed in today",
    "type": "already_signed_in",
    "param": null,
    "code": "already_signed_in"
  }
}
```

### 3. 成功/失败判断
- **成功**: HTTP 200，响应中包含 `reward` 和 `balance` 字段
- **失败**: HTTP 4xx，响应中包含 `error` 对象，`error.code` 为 `already_signed_in` 表示今日已签到

### 完整 curl 示例
```bash
# 登录
RESPONSE=$(curl -s -X POST "https://lizhiyu.appleinc.cn/v1/user/login-pwd" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"email":"2898263796@qq.com","password":"youqisi1314"}')
TOKEN=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 签到
curl -s -X POST "https://lizhiyu.appleinc.cn/v1/user/signin" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{}'
```

### 其他可用API端点
| 端点 | 说明 |
|------|------|
| `/v1/user/send-code` | 发送QQ邮箱验证码 |
| `/v1/user/register-login` | 验证码注册/登录 |
| `/v1/user/register-direct` | 密码直接注册 |
| `/v1/user/stats` | 获取用户统计 |
| `/v1/user/keys` | 获取API密钥列表 |
| `/v1/user/profile` | 获取用户资料 |
| `/v1/user/update-pwd` | 修改密码 |
| `/v1/user/rank` | 获取排行榜 |
| `/v1/models` | 获取模型列表 |

---

## 站点3: binmt论坛 / MT论坛 (bbs.binmt.cc)

### 平台类型
Discuz! X3.4 论坛 + k_misign 签到插件

### 1. 登录接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1` |
| **方法** | POST |
| **Content-Type** | application/x-www-form-urlencoded |
| **请求体** | `username=15256386374&password=youqisi1314&quickforward=yes&handlekey=login` |

**登录响应 (XML):**
```xml
<?xml version="1.0" encoding="utf-8"?>
<root><![CDATA[<script type="text/javascript" reload="1">
if(typeof succeedhandle_login=='function') {succeedhandle_login('./', '手机号登录成功', {});}
hideWindow('login');
showDialog('手机号登录成功', 'notice', null, function () { window.location.href ='./'; }, 0, null, null, null, null, null, 2);
</script>]]></root>
```

**认证方式:**
- 登录成功后通过 `Set-Cookie` 返回多个 cookie
- 关键 cookie: `cQWy_2132_auth` (用户认证, HttpOnly) 和 `cQWy_2132_saltkey` (会话salt)
- Cookie 前缀: `cQWy_2132_` (由页面JS变量 `cookiepre` 定义)
- 后续请求需要携带所有 cookie

### 2. 签到接口

| 项目 | 值 |
|------|-----|
| **URL** | `https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&formhash=<formhash>&format=empty` |
| **方法** | GET |
| **请求头** | `Cookie: <登录后的所有cookie>` |
| **请求体** | 无 |

**重要参数说明:**
- `formhash`: CSRF令牌，需要从签到页面 (`k_misign-sign.html`) 中提取，HTML中有 `<input type="hidden" name="formhash" value="f6d23573" />`
- `format=empty`: 返回简洁的XML响应
- `operation=qiandao`: 签到操作标识

**获取 formhash 的方式:**
```bash
# 先访问签到页面，从HTML中提取formhash
curl -s -b /tmp/binmt_cookie "https://bbs.binmt.cc/k_misign-sign.html" | grep -oP 'formhash" value="\K[^"]+'
```

**签到成功响应 (XML):**
```xml
<?xml version="1.0" encoding="utf-8"?>
<root><![CDATA[]]></root>
```
空CDATA内容表示签到成功。

**未登录时签到响应:**
HTML页面中显示 "您需要先登录才能继续本操作"

### 3. 成功/失败判断
- **成功**: HTTP 200，XML响应中 `<root><![CDATA[]]></root>` (空CDATA)
- **失败 (未登录)**: HTTP 200，HTML页面显示 "您需要先登录才能继续本操作"
- **失败 (已签到)**: HTTP 200，XML响应中包含错误提示信息

### 完整 curl 示例
```bash
# 登录
curl -s -v -c /tmp/binmt_cookie -X POST \
  "https://bbs.binmt.cc/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1" \
  -d "username=15256386374&password=youqisi1314&quickforward=yes&handlekey=login"

# 获取 formhash
FORMHASH=$(curl -s -b /tmp/binmt_cookie "https://bbs.binmt.cc/k_misign-sign.html" | grep -oP 'formhash" value="\K[^"]+')

# 签到
curl -s -b /tmp/binmt_cookie \
  "https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&formhash=${FORMHASH}&format=empty"
```

---

## 三站点对比总结

| 特性 | 站点1 (哈基米) | 站点2 (荔枝鱼) | 站点3 (binmt) |
|------|---------------|---------------|--------------|
| **平台** | New API / one-api | 自定义 Vue3 + API | Discuz! X3.4 + k_misign |
| **登录方法** | POST JSON | POST JSON | POST form-urlencoded |
| **登录字段** | username + password | email + password | username + password |
| **认证方式** | Cookie + Header (New-Api-User) | Bearer Token | Cookie (Discuz auth) |
| **签到方法** | POST | POST | GET |
| **签到需要CSRF** | 否 | 否 | 是 (formhash) |
| **签到成功判断** | success:true | reward字段 | 空XML CDATA |
| **签到失败判断** | success:false + message | error.code | XML错误信息 |
