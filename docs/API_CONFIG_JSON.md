# 站点配置 JSON 标准格式文档

> 版本: v2.0  
> 适用: 全自动签到助手 - 自定义 API 站点配置

---

## 1. 概述

本文档定义了全自动签到助手系统中，**自定义 API 站点**的 JSON 配置标准格式。通过此格式，您可以：

- **导入站点**：将 AI 生成的配置或他人分享的模板直接粘贴导入系统
- **导出站点**：将已配置好的站点导出为 JSON，方便备份或分享
- **批量操作**：一次性导入多个站点配置

---

## 2. 标准 JSON 格式

### 2.1 单站点配置格式

```json
{
  "name": "站点原始名称",
  "display_name": "管理页面显示名称（可选）",
  "category": "分类名称",
  "type": "custom-api",
  "url": "https://example.com",
  "api_config": {
    "login_url": "https://api.example.com/v1/login",
    "login_method": "POST",
    "login_body_template": "{\"username\": \"{{username}}\", \"password\": \"{{password}}\"}",
    "login_content_type": "application/json",
    "login_extra_headers": {},
    "token_path": "data.token",
    "signin_url": "https://api.example.com/v1/signin",
    "signin_method": "POST",
    "signin_body": "{}",
    "signin_content_type": "application/json",
    "signin_extra_headers": {},
    "auth_header_template": "Bearer {{token}}",
    "auth_header_name": "Authorization",
    "success_field": "success",
    "message_field": "message",
    "force_login": false,
    "login_only": false,
    "verify_ssl": true,
    "extra_headers": {}
  }
}
```

### 2.2 多站点批量格式

```json
[
  {
    "name": "站点A",
    "type": "custom-api",
    "api_config": { ... }
  },
  {
    "name": "站点B",
    "type": "custom-api",
    "api_config": { ... }
  }
]
```

或带 `sites` 包裹的格式：

```json
{
  "sites": [
    { "name": "站点A", "type": "custom-api", "api_config": { ... } },
    { "name": "站点B", "type": "custom-api", "api_config": { ... } }
  ]
}
```

---

## 3. 字段详解

### 3.1 顶层字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `name` | string | 是 | 站点原始名称（如 API 文档中的名称） |
| `display_name` | string | 否 | 管理页面显示的自定义名称，为空时显示 `name` |
| `category` | string | 否 | 分类标签，如 "API服务"、"公益站点"、"论坛社区" 等 |
| `type` | string | 是 | 站点类型，自定义 API 站点固定为 `"custom-api"` |
| `url` | string | 否 | 站点官网地址 |
| `api_config` | object | 是 | API 签到配置详情（见下方） |

### 3.2 api_config 字段详解

#### 登录配置

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `login_url` | string | `""` | 登录接口地址，如 `https://api.example.com/v1/login` |
| `login_method` | string | `"POST"` | 登录请求方法：`POST` / `GET` / `PUT` |
| `login_body_template` | string | 见示例 | 登录请求体模板，支持 `{{username}}` 和 `{{password}}` 占位符 |
| `login_content_type` | string | `"application/json"` | 登录请求的 Content-Type |
| `login_extra_headers` | object | `{}` | 登录请求的额外请求头 |

#### Token 提取配置

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `token_path` | string | `"token"` | 从登录响应中提取 token 的字段路径，支持嵌套，如 `data.token`、`result.user.id` |

#### 签到配置

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `signin_url` | string | `""` | 签到接口地址 |
| `signin_method` | string | `"POST"` | 签到请求方法：`POST` / `GET` / `PUT` |
| `signin_body` | string | `"{}"` | 签到请求体（JSON 字符串） |
| `signin_content_type` | string | `"application/json"` | 签到请求的 Content-Type |
| `signin_extra_headers` | object | `{}` | 签到请求的额外请求头 |

#### 认证配置

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `auth_header_template` | string | `"Bearer {{token}}"` | 认证头值模板，`{{token}}` 会被替换为提取到的 token |
| `auth_header_name` | string | `"Authorization"` | 认证头的字段名，如 `Authorization`、`X-Api-User` |

#### 响应解析配置

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `success_field` | string | `""` | 判断签到是否成功的字段路径，为空时不检查 |
| `message_field` | string | `""` | 从响应中提取提示消息的字段路径 |

#### 高级选项

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `force_login` | boolean | `false` | 强制登录：即使账号已有 token 也重新登录 |
| `login_only` | boolean | `false` | 登录即签到：该站点登录成功即视为签到完成 |
| `verify_ssl` | boolean | `true` | 是否验证 SSL 证书 |
| `extra_headers` | object | `{}` | 全局额外请求头（登录和签到都会携带） |

---

## 4. 模板变量说明

在 `login_body_template` 和 `auth_header_template` 中，支持以下占位符：

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{{username}}` | 账号的用户名 | 自动替换为账号管理中的 `username` |
| `{{password}}` | 账号的密码 | 自动替换为账号管理中的 `password` |
| `{{token}}` | 登录后提取的 token | 仅在 `auth_header_template` 中可用 |

---

## 5. 完整示例

### 示例 1：标准登录 + 签到流程

某 API 站点需要：先登录获取 token，再用 token 调用签到接口。

```json
{
  "name": "示例API站",
  "display_name": "我的示例站",
  "category": "API服务",
  "type": "custom-api",
  "url": "https://api.example.com",
  "api_config": {
    "login_url": "https://api.example.com/v1/auth/login",
    "login_method": "POST",
    "login_body_template": "{\"email\": \"{{username}}\", \"password\": \"{{password}}\"}",
    "login_content_type": "application/json",
    "token_path": "data.token",
    "signin_url": "https://api.example.com/v1/user/signin",
    "signin_method": "POST",
    "signin_body": "{}",
    "signin_content_type": "application/json",
    "auth_header_template": "Bearer {{token}}",
    "auth_header_name": "Authorization",
    "success_field": "success",
    "message_field": "message",
    "verify_ssl": true
  }
}
```

**执行流程：**
1. POST `https://api.example.com/v1/auth/login`  
   Body: `{"email": "用户账号", "password": "用户密码"}`
2. 从响应中提取 `data.token`（如响应为 `{"data": {"token": "abc123"}}`）
3. POST `https://api.example.com/v1/user/signin`  
   Header: `Authorization: Bearer abc123`
4. 检查 `success` 字段判断结果，提取 `message` 显示提示

### 示例 2：登录即签到（无独立签到接口）

某些站点登录成功即完成签到，无需额外调用签到接口。

```json
{
  "name": "登录即签到站",
  "display_name": "一键签到站",
  "category": "公益站点",
  "type": "custom-api",
  "url": "https://demo.com",
  "api_config": {
    "login_url": "https://demo.com/api/login",
    "login_method": "POST",
    "login_body_template": "{\"username\": \"{{username}}\", \"password\": \"{{password}}\"}",
    "login_content_type": "application/json",
    "token_path": "token",
    "signin_url": "",
    "signin_method": "POST",
    "signin_body": "{}",
    "auth_header_template": "",
    "auth_header_name": "",
    "success_field": "code",
    "message_field": "msg",
    "login_only": true,
    "verify_ssl": true
  }
}
```

**关键点：** `login_only: true` + `signin_url` 为空  
系统会：登录 → 检查响应 → 直接返回成功

### 示例 3：Cookie 模式（无 Token）

某些站点使用 Cookie 会话，不需要提取 token。

```json
{
  "name": "Cookie签到站",
  "display_name": "论坛签到",
  "category": "论坛社区",
  "type": "custom-api",
  "url": "https://bbs.example.com",
  "api_config": {
    "login_url": "https://bbs.example.com/api/login",
    "login_method": "POST",
    "login_body_template": "username={{username}}&password={{password}}",
    "login_content_type": "application/x-www-form-urlencoded",
    "token_path": "",
    "signin_url": "https://bbs.example.com/api/signin",
    "signin_method": "GET",
    "signin_body": "",
    "signin_content_type": "application/json",
    "auth_header_template": "",
    "auth_header_name": "",
    "success_field": "",
    "message_field": "message",
    "verify_ssl": true
  }
}
```

**关键点：** `token_path` 为空，系统会自动使用 Cookie 会话继续调用签到接口。

### 示例 4：自定义认证头

某些站点使用非标准的认证方式。

```json
{
  "name": "自定义认证站",
  "display_name": "特殊认证站",
  "category": "工具网站",
  "type": "custom-api",
  "url": "https://tool.example.com",
  "api_config": {
    "login_url": "https://tool.example.com/api/auth",
    "login_method": "POST",
    "login_body_template": "{\"user\": \"{{username}}\", \"pass\": \"{{password}}\"}",
    "token_path": "result.api_key",
    "signin_url": "https://tool.example.com/api/daily",
    "signin_method": "POST",
    "signin_body": "{}",
    "auth_header_template": "{{token}}",
    "auth_header_name": "X-API-Key",
    "success_field": "status",
    "message_field": "info",
    "verify_ssl": true
  }
}
```

**关键点：** `auth_header_name: "X-API-Key"` + `auth_header_template: "{{token}}"`  
签到请求头会变成：`X-API-Key: 提取到的token值`

---

## 6. 导入方式

### 方式一：前端粘贴导入

1. 进入「网站管理」页面
2. 点击右上角「粘贴JSON导入」按钮
3. 将上述 JSON 配置粘贴到文本框中
4. 点击「导入」按钮

### 方式二：后端 API 导入

```bash
curl -X POST "https://your-domain/api/sites" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例站",
    "type": "custom-api",
    "api_config": { ... }
  }'
```

### 方式三：批量导入

```bash
curl -X POST "https://your-domain/api/sites/bulk" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sites": [
      { "name": "站A", "type": "custom-api", "api_config": { ... } },
      { "name": "站B", "type": "custom-api", "api_config": { ... } }
    ]
  }'
```

---

## 7. 常见问题

### Q1: 如何确定 `token_path`？

查看登录接口的响应 JSON，找到 token 所在的位置：

```json
// 响应示例 1: 简单结构
{"token": "abc123"}           → token_path: "token"

// 响应示例 2: 嵌套结构
{"data": {"token": "abc123"}} → token_path: "data.token"

// 响应示例 3: 多层嵌套
{"result": {"user": {"api_key": "abc123"}}} → token_path: "result.user.api_key"
```

### Q2: 站点没有登录接口怎么办？

如果账号已有 token 或 cookie，可以将 `login_url` 留空，系统在签到时会直接使用账号保存的 token。

### Q3: 如何调试配置？

添加站点后，点击操作栏的「测试」按钮，输入测试账号密码即可验证配置是否正确。

---

## 8. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2024-XX-XX | 初始版本，支持基本登录+签到流程 |
| v2.0 | 2025-06-12 | 新增 Cookie 支持、自定义认证头、SSL 开关、登录即签到模式 |
