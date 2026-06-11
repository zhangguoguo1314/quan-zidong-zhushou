# 全自动助手 — 部署指南

本项目采用 **前后端分离** 架构，所有静态文件由 Nginx / Vite 提供，API 请求由 Python FastAPI 提供。

```
浏览器 ──▶ 前端静态页面 (端口 3000 或 8080)
   │
   └──▶ /api/* ──▶ 后端 FastAPI (端口 8000)
```

## 目录

- [环境要求](#环境要求)
- [方式一：Docker Compose（推荐，最省心）](#方式一docker-compose推荐最省心)
- [方式二：Linux / 服务器部署（含一键脚本）](#方式二linux-服务器部署含一键脚本)
- [方式三：macOS 部署（含一键脚本）](#方式三macos-部署含一键脚本)
- [方式四：Windows 部署（含一键脚本）](#方式四windows-部署含一键脚本)
- [方式五：Android 手机 + WSToolbox 部署（见独立文档）](#方式五android-手机--wstoolbox-部署见独立文档)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 环境要求

| 组件 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.11+ | 后端运行时，建议 3.11 / 3.12 |
| Node.js | 20+ | 前端构建，建议 20 LTS 或 22 |
| npm | 10+ | 随 Node.js 一起安装 |
| SQLite | 系统内置 | 数据库文件，无需单独安装 |
| （可选）Docker | 25+ | 容器化部署 |
| （可选）Playwright Chromium | - | 自动签到浏览器内核 |

硬件最低配置：

- CPU：1 核以上（2 核起步体验更好）
- 内存：512MB（Playwright 运行时建议 1GB 以上）
- 磁盘：500MB 可用空间（依赖 + 静态文件）

---

## 方式一：Docker Compose（推荐，最省心）

### 1. 准备服务器

任何支持 Docker 的 Linux 服务器（Ubuntu 20.04+、Debian 11+、CentOS 8+）都可以。

```bash
# 安装 Docker（Ubuntu/Debian 示例）
curl -fsSL https://get.docker.com | sh

# 安装 docker-compose
apt install -y docker-compose
# 或
pip install docker-compose
```

### 2. 获取代码并启动

```bash
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou

# （可选）编辑邮件配置
cp backend/.env.example backend/.env
vim backend/.env

# 一键构建并启动
docker-compose up --build -d

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问

- 前端界面：http://服务器IP:3000
- 后端 API：http://服务器IP:8000
- 接口文档：http://服务器IP:8000/docs

### 4. 停止与更新

```bash
# 停止服务
docker-compose down

# 更新代码后重启
git pull
docker-compose up --build -d
```

---

## 方式二：Linux / 服务器部署（含一键脚本）

适用于 Ubuntu 20.04+、Debian 11+、CentOS 8+。

### 1. 安装基础环境

**Ubuntu / Debian：**

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Python 3.11+ 和 Node.js 20+
apt install -y python3 python3-pip python3-venv curl
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 验证
python3 --version   # 期望 Python 3.11.x
node --version      # 期望 v20.x.x
npm --version       # 期望 10.x.x
```

**CentOS / RHEL：**

```bash
# 安装 EPEL 源
yum install -y epel-release

# 安装 Python 3.11（从源码或 SCL）
yum install -y python3.11 python3.11-pip

# 安装 Node.js 20
curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
yum install -y nodejs
```

### 2. 一键安装项目依赖

```bash
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou

# 赋予脚本执行权限
chmod +x scripts/*.sh

# 一键安装（自动创建虚拟环境、装依赖、构建前端）
bash scripts/install-linux.sh
```

这个脚本会自动做：

1. 检查 Python 3.11+ 和 Node.js 20+ 是否已安装
2. 创建 `.venv` Python 虚拟环境
3. 安装 `backend/requirements.txt` 中的 Python 依赖
4. 自动安装 Playwright Chromium 浏览器（用于签到）
5. 复制 `backend/.env.example` 为 `backend/.env`
6. 安装前端 `npm` 依赖并构建静态文件到 `frontend/dist`

### 3. 配置（可选但推荐）

```bash
cd backend
cp .env.example .env
vim .env
```

关键配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| SECRET_KEY | JWT 签名密钥，**必须修改** | `your-secret-key-change-in-production` |
| DATABASE_URL | SQLite 数据库文件路径 | `sqlite:///data/data.db` |
| SMTP_HOST | 邮件服务器地址 | `smtp.gmail.com` |
| SMTP_PORT | 邮件服务器端口 | 587 |
| SMTP_USER | 邮箱账号 | - |
| SMTP_PASSWORD | 邮箱授权码（不是登录密码） | - |
| EMAIL_FROM | 发件人显示邮箱 | - |
| PLAYWRIGHT_HEADLESS | 是否无头模式运行浏览器 | `true` |

### 4. 启动服务

**方式 A：一键启动脚本（推荐新手）**

```bash
# 同时启动后端和前端静态服务器
bash scripts/start-linux.sh
```

**方式 B：手动分步启动（适合调试）**

终端 1 — 启动后端：

```bash
source .venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

终端 2 — 启动前端（开发模式）：

```bash
cd frontend
npm run dev          # 开发模式，端口 5173
# 或
npm run build && npm run preview   # 生产模式，端口 4173
```

**方式 C：使用 Nginx 托管前端（生产环境推荐）**

```bash
apt install -y nginx
cp frontend/nginx.conf /etc/nginx/conf.d/auto-sign.conf
# 修改 nginx.conf 中的端口、路径、后端代理地址
nginx -s reload
```

### 5. 使用 systemd 守护进程（生产环境）

```bash
# /etc/systemd/system/auto-sign-backend.service
cat > /etc/systemd/system/auto-sign-backend.service << 'EOF'
[Unit]
Description=Auto Sign Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/quan-zidong-zhushou/backend
ExecStart=/path/to/quan-zidong-zhushou/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable auto-sign-backend
systemctl start auto-sign-backend
```

---

## 方式三：macOS 部署（含一键脚本）

### 1. 安装基础环境

使用 Homebrew 最方便：

```bash
# 安装 Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python 和 Node.js
brew install python@3.11 node@20

# 验证
python3 --version
node --version
npm --version
```

### 2. 一键安装

```bash
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
chmod +x scripts/*.sh
bash scripts/install-macos.sh
```

### 3. 启动服务

```bash
bash scripts/start-macos.sh
```

macOS 访问地址：

- 前端：http://localhost:5173（开发模式）
- 前端：http://localhost:4173（生产预览）
- 后端：http://localhost:8000
- 接口文档：http://localhost:8000/docs

---

## 方式四：Windows 部署（含一键脚本）

### 1. 安装基础环境

- 下载安装 Python 3.11+：https://www.python.org/downloads/
  - 安装时 **务必勾选** "Add Python to PATH"
- 下载安装 Node.js 20 LTS：https://nodejs.org/
  - 安装包自动配置 PATH

安装后打开 PowerShell 验证：

```powershell
python --version    # Python 3.11.x
node --version      # v20.x.x
npm --version       # 10.x.x
```

### 2. 一键安装（PowerShell）

```powershell
# 进入项目目录
cd quan-zidong-zhushou

# 允许脚本执行（首次运行需要，打开 PowerShell 管理员身份）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser

# 运行安装脚本
powershell -ExecutionPolicy Bypass -File scripts\install-windows.ps1
```

### 3. 启动服务

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1
```

Windows 访问地址同 macOS。

### 4. Windows 上的注意事项

- 如果浏览器内核下载失败，可以设置国内镜像：`$env:PLAYWRIGHT_DOWNLOAD_HOST="https://npmmirror.com/mirrors/playwright/"`
- `pip install` 失败时尝试：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
- `npm install` 失败时尝试：`npm config set registry https://registry.npmmirror.com`

---

## 方式五：Android 手机 + WSToolbox 部署

**请查看独立文档：[WSTOOLBOX.md](./WSTOOLBOX.md)**

核心思路：

- WSToolbox 的 Nginx 托管前端静态文件
- Termux 运行 Python FastAPI 后端
- Nginx 将 `/api/*` 请求反向代理到本地的 `127.0.0.1:8000`
- 手机浏览器访问 http://手机IP:8080 即可使用

---

## 配置说明

### 修改端口

默认端口：

- 后端 API：8000
- 前端开发：5173
- 前端生产（Nginx/Docker）：3000
- WSToolbox：8080

修改方法：

**改后端端口** — 修改启动命令：

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

同时修改前端 `frontend/nginx.conf` 中的 `proxy_pass http://backend:8001;`

**改前端端口** — 修改 `frontend/vite.config.ts`：

```ts
server: {
  port: 3000,
  // ...
}
```

### 修改数据库路径

编辑 `backend/.env`：

```env
DATABASE_URL=sqlite:///data/data.db
```

SQLite 是文件型数据库，路径相对于 `backend/` 目录。
首次启动会自动创建数据库文件和表结构。

### 邮件通知配置

以 QQ 邮箱为例：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your-qq@qq.com
SMTP_PASSWORD=你的QQ邮箱授权码   # 注意：不是登录密码，是授权码
EMAIL_FROM=your-qq@qq.com
```

以 163 邮箱为例：

```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your-163@163.com
SMTP_PASSWORD=你的163邮箱授权码
EMAIL_FROM=your-163@163.com
```

以 Gmail 为例（需要应用专用密码）：

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=你的Gmail应用专用密码
EMAIL_FROM=your@gmail.com
```

### 生产环境安全建议

1. **务必修改 `SECRET_KEY`**：使用随机字符串，例如 `openssl rand -hex 32` 生成
2. **使用 HTTPS**：如果部署到公网服务器，配置 Nginx + Let's Encrypt
3. **限制端口暴露**：后端不要直接暴露到公网，只让 Nginx 反向代理访问
4. **定期备份**：备份 `backend/data/data.db` 数据库文件
5. **定期更新**：`git pull` 更新代码，重建依赖

---

## 常见问题

### Q1：启动后前端页面空白或 404

**原因**：前端静态文件未正确构建或 Nginx 路径配置错误。

**解决**：

```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
# 确认 dist/index.html 存在
ls dist/index.html
```

### Q2：后端报 "No module named 'fastapi'"

**原因**：未激活虚拟环境，或依赖未安装。

**解决**：

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Q3：Playwright 下载浏览器失败

**原因**：网络问题，无法下载 Chromium 内核。

**解决**：

```bash
# 国内镜像
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ playwright install chromium

# 或者使用系统浏览器（需要系统已安装 Chrome / Chromium）
PLAYWRIGHT_BROWSERS_PATH=0 playwright install chromium
```

### Q4：签到任务未执行

**原因**：APScheduler 任务未启动，或 Cron 表达式错误。

**排查**：

1. 确认后端正常运行，访问 http://localhost:8000/api/health 返回 `{"status": "healthy"}`
2. 在系统中添加定时任务后，查看后端日志确认任务被调度
3. Cron 表达式格式：`分 时 日 月 周`，例如 `0 8 * * *` 表示每天早上 8 点

### Q5：数据库被锁（SQLite 多进程问题）

**原因**：多个 Python 进程同时写入 SQLite。

**解决**：

```bash
# 停止所有服务，确认没有残留进程
ps aux | grep uvicorn
kill <进程ID>

# 重新启动
bash scripts/start-linux.sh
```

### Q6：忘记密码怎么办

目前 V1 没有"忘记密码"功能。可以直接操作 SQLite 数据库重置：

```bash
cd backend
python3 -c "
import sqlite3
from passlib.context import CryptContext
pwd = CryptContext(schemes=['bcrypt'])
conn = sqlite3.connect('data/data.db')
new_hash = pwd.hash('newpassword123')
conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
conn.commit()
print('密码已重置为: newpassword123')
"
```

---

## 端口参考表

| 部署方式 | 前端端口 | 后端端口 | 访问地址 |
|---------|---------|---------|---------|
| Docker Compose | 3000 | 8000 | http://localhost:3000 |
| Vite 开发模式 | 5173 | 8000 | http://localhost:5173 |
| Vite 生产预览 | 4173 | 8000 | http://localhost:4173 |
| Nginx 托管前端 | 80/8080 | 8000（内部） | http://服务器IP |
| WSToolbox + Termux | 8080 | 8000（内部） | http://手机IP:8080 |

## 下一步

部署完成后，请访问 **README.md** 中的"功能使用指南"部分，开始配置你的第一个签到网站和账号。
