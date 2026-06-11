# 全自动助手

多网站多账号自动签到平台 — 一次配置，自动签到。

## 简介

全自动助手（Auto-Sign）是一个开源的自动签到平台。你可以：

- 在界面中添加要签到的网站和账号
- 设置定时任务（Cron 表达式）
- 系统到时间自动完成签到
- 签到结果记录在日志中，失败时可邮件通知
- 可部署在电脑、服务器、甚至安卓手机上

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11 + FastAPI + SQLAlchemy + APScheduler |
| **前端** | Vue 3 + TypeScript + Element Plus + Pinia + Vue Router + Vite |
| **数据库** | SQLite（单文件，无需单独部署） |
| **部署** | Docker / 原生脚本 / Android 手机 (WSToolbox + Termux) |
| **签到引擎** | Playwright / 自定义插件 |

---

## 功能特性

- 用户系统 — 注册、登录、JWT 认证
- 网站管理 — 添加/编辑/删除网站，支持多种网站类型
- 账号管理 — 添加账号、CSV 批量导入、支持用户名密码/Token/Cookie
- 定时任务 — Cron 表达式调度，灵活设置签到时间
- 签到日志 — 查看每次签到结果，支持筛选和删除
- 邮件通知 — 签到失败自动发邮件提醒
- 插件系统 — 支持自定义 Python 签到脚本
- 多端部署 — 支持 Windows / macOS / Linux / Docker / Android 手机

---

## 项目结构

```
quan-zidong-zhushou/
├── backend/              # Python FastAPI 后端
│   ├── api/routes/      # API 路由 (auth, sites, accounts, tasks, logs)
│   ├── models/          # SQLAlchemy 数据模型
│   ├── schemas/         # Pydantic 请求/响应定义
│   ├── services/        # 业务逻辑服务 (scraper, notification)
│   ├── plugins/         # 签到插件系统
│   ├── tasks/           # APScheduler 任务调度
│   ├── core/            # 配置、数据库、安全
│   ├── main.py          # FastAPI 入口
│   ├── requirements.txt # Python 依赖
│   └── .env.example     # 配置模板
├── frontend/            # Vue 3 前端
│   ├── src/
│   │   ├── pages/       # 页面组件 (登录、仪表盘、网站、账号、任务、日志、设置)
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── api/         # Axios API 客户端
│   │   └── router/      # Vue Router 路由
│   ├── vite.config.ts   # Vite 配置（已包含 /api 反向代理）
│   ├── Dockerfile       # 前端 Docker 镜像
│   └── nginx.conf       # 生产环境 Nginx 配置
├── docs/                # 部署文档
│   ├── DEPLOY.md        # 全环境部署指南
│   ├── WSTOOLBOX.md     # Android 手机部署指南
│   └── wstoolbox-nginx.conf  # 手机 Nginx 配置模板
├── scripts/             # 一键脚本
│   ├── install-linux.sh
│   ├── start-linux.sh
│   ├── install-macos.sh
│   ├── start-macos.sh
│   ├── install-windows.ps1
│   ├── start-windows.ps1
│   ├── install-termux.sh
│   ├── start-termux.sh
│   └── deploy-wstoolbox.sh   # 手机一键部署
├── docker-compose.yml   # Docker 一键部署
└── README.md
```

---

## 快速开始

### 方式一：Docker Compose（最简单）

```bash
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
docker-compose up --build
```

访问 http://localhost:3000

### 方式二：本地开发（Linux / macOS）

```bash
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
bash scripts/install-linux.sh   # 或 install-macos.sh
bash scripts/start-linux.sh     # 或 start-macos.sh
```

访问 http://localhost:5173

### 方式三：Windows

```powershell
cd quan-zidong-zhushou
powershell -ExecutionPolicy Bypass -File scripts\install-windows.ps1
powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1
```

### 方式四：纯 Termux 部署到安卓手机

**完整教程：[docs/TERMUX.md](docs/TERMUX.md)**

```bash
# 在手机的 Termux 中执行
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
bash scripts/deploy-termux.sh
```

手机浏览器访问 http://127.0.0.1:8080

### 方式五：WSToolbox + Termux 部署到安卓手机

**完整教程：[docs/WSTOOLBOX.md](docs/WSTOOLBOX.md)**

```bash
# 在手机的 Termux 中执行
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
bash scripts/deploy-wstoolbox.sh
```

手机浏览器访问 http://127.0.0.1:8080

---

## 详细部署文档

- 全环境部署指南（Linux/macOS/Windows/Docker）：[docs/DEPLOY.md](docs/DEPLOY.md)
- Android 纯 Termux 部署指南：[docs/TERMUX.md](docs/TERMUX.md)
- Android 手机部署指南（WSToolbox + Termux）：[docs/WSTOOLBOX.md](docs/WSTOOLBOX.md)

---

## 端口参考

| 部署方式 | 前端端口 | 后端端口 | 访问地址 |
|---------|---------|---------|---------|
| Docker Compose | 3000 | 8000 | http://localhost:3000 |
| 本地开发 (Vite) | 5173 | 8000 | http://localhost:5173 |
| Nginx 托管前端 | 80/3000 | 8000（内部） | http://服务器IP |
| 纯 Termux | 8080 | 8000（内部） | http://手机IP:8080 |
| WSToolbox + Termux | 8080 | 8000（内部） | http://手机IP:8080 |

---

## 功能使用指南

### 1. 注册登录

1. 打开首页 → 点击"注册"
2. 输入用户名和密码 → 提交
3. 用刚注册的账号登录

### 2. 添加网站

1. 左侧菜单 → "网站管理" → "添加网站"
2. 填写：
   - **名称**：比如 "某论坛"
   - **类型**：选择网站类型（决定使用哪个签到插件）
   - **登录 URL**：网站登录页地址
3. 保存

### 3. 添加账号

1. 左侧菜单 → "账号管理" → "添加账号"
2. 选择所属网站，填写登录信息：
   - 用户名 + 密码
   - 或 Token
   - 或 Cookie（从浏览器复制粘贴）
3. 保存

**批量导入**：账号管理 → "CSV 导入"，上传符合格式的 CSV 文件即可批量添加

### 4. 设置定时任务

1. 左侧菜单 → "任务管理" → "添加任务"
2. 选择账号，设置 Cron 表达式

常见 Cron 示例：

| 表达式 | 含义 |
|--------|------|
| `0 8 * * *` | 每天早上 8 点 |
| `0 9,21 * * *` | 每天 9 点和 21 点各一次 |
| `30 7 * * 1-5` | 工作日（周一到周五）早上 7:30 |
| `0 0 * * 0` | 每周日凌晨 0 点 |

### 5. 查看签到结果

左侧菜单 → "签到日志"

可以按账号、时间范围、成功/失败筛选。点击记录查看详细信息。

### 6. 配置邮件通知（可选）

1. 编辑 `backend/.env`
2. 填写 SMTP 服务器信息
3. 重启后端服务

示例配置（QQ 邮箱）：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your@qq.com
SMTP_PASSWORD=你的邮箱授权码
EMAIL_FROM=your@qq.com
```

---

## API 接口

后端启动后，访问 http://localhost:8000/docs 查看完整的 Swagger API 文档。

主要接口：

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录（返回 JWT token） |
| `/api/sites` | GET | 网站列表 |
| `/api/sites` | POST | 添加网站 |
| `/api/accounts` | GET | 账号列表 |
| `/api/accounts` | POST | 添加账号 |
| `/api/accounts/import` | POST | CSV 批量导入账号 |
| `/api/tasks` | GET | 任务列表 |
| `/api/tasks` | POST | 添加定时任务 |
| `/api/logs` | GET | 签到日志 |
| `/api/health` | GET | 健康检查 |

---

## 开发进度 — 当前阶段

### V1 — 核心功能（当前阶段，已完成主要骨架）

- 用户系统（注册/登录/JWT）✅
- 网站管理（CRUD）✅
- 账号管理（CRUD + CSV 导入）✅
- 定时任务（Cron 调度）✅
- 签到日志（查看/筛选/删除）✅
- 邮件通知服务 ✅
- Playwright 签到引擎 ✅
- 插件系统（支持自定义签到逻辑）✅
- 前后端分离架构 ✅
- Docker 部署 ✅
- Windows / macOS / Linux 一键脚本 ✅
- Android 手机部署（WSToolbox + Termux）✅

**接下来需要你做的**：

1. **跑起来验证** — 在你的机器/手机上执行安装脚本，确认服务能正常启动
2. **写你需要的签到插件** — `backend/plugins/` 目录下自定义你要签到的网站逻辑
3. **填入真实账号和任务** — 登录界面后添加你的网站和账号

### V2 — 规划中（欢迎提建议）

- 多用户角色与权限隔离
- 签到任务手动触发（立即执行按钮）
- 更丰富的日志统计图表（成功率趋势、热力图）
- 微信/飞书/钉钉通知
- 网站登录验证码识别（接入 OCR 或人工标记）
- 账号操作审计日志
- 一键更新系统

---

## 配置参考

编辑 `backend/.env` 文件：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | 请修改 | JWT 签名密钥，生产环境务必修改 |
| `DATABASE_URL` | `sqlite:///data/data.db` | SQLite 数据库文件路径 |
| `SMTP_HOST` | - | 邮件服务器地址 |
| `SMTP_PORT` | 587 | 邮件服务器端口 |
| `SMTP_USER` | - | 邮箱账号 |
| `SMTP_PASSWORD` | - | 邮箱授权码（不是登录密码） |
| `EMAIL_FROM` | - | 发件人显示邮箱 |
| `PLAYWRIGHT_HEADLESS` | `true` | 是否无头模式运行浏览器 |

---

## 常见问题

**Q: 忘记密码怎么办？**

直接操作 SQLite 重置：

```bash
cd backend
python3 -c "
import sqlite3
from passlib.context import CryptContext
pwd = CryptContext(schemes=['bcrypt'])
conn = sqlite3.connect('data/data.db')
new_hash = pwd.hash('newpassword123')
conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, '你的用户名'))
conn.commit()
print('密码已重置为: newpassword123')
"
```

**Q: 签到任务到点没执行？**

1. 确认后端在运行：`curl http://localhost:8000/api/health`
2. 检查 Cron 表达式格式是否正确（标准 5 段式：分 时 日 月 周）
3. 查看后端日志：`tail -f backend.log`

**Q: Playwright 浏览器下载失败？**

使用国内镜像：

```bash
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ playwright install chromium
```

**Q: 更多问题？**

查看详细部署文档：
- [docs/DEPLOY.md](docs/DEPLOY.md) — 全环境部署指南 + FAQ
- [docs/WSTOOLBOX.md](docs/WSTOOLBOX.md) — 手机部署指南 + FAQ

---

## 许可证

MIT License — 可自由使用、修改、分发。
