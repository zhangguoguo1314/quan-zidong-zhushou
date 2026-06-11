# Android 手机纯 Termux 部署指南

这份文档只使用 **Termux** 部署“全自动助手”，不依赖 WSToolbox。Termux 负责运行 Python FastAPI 后端，也负责运行 Nginx 来托管前端静态页面并反向代理 `/api` 请求。

```
手机浏览器 / 局域网设备
        │
        ▼
Termux Nginx :8080
        ├── 前端静态页面 frontend/dist
        └── /api/* 反向代理到 FastAPI :8000
```

## 适用场景

纯 Termux 方案适合只想安装一个 App 的用户。它比 WSToolbox 方案更轻，所有运行文件都放在 Termux 的用户目录里；缺点是 Nginx 配置和后台保活都要在 Termux 里完成。

| 方案 | 需要安装 | 访问端口 | 适合 |
|------|----------|----------|------|
| 纯 Termux | Termux | 8080 | 只想装一个 App、喜欢命令行 |
| WSToolbox + Termux | WSToolbox、Termux | 8080 | 想用图形界面管理 Nginx |
| 云服务器 | Linux、Docker | 3000/80 | 长期稳定公网使用 |

## 手机环境要求

| 项目 | 建议 |
|------|------|
| Android 版本 | Android 7.0 以上，推荐 Android 10+ |
| CPU | 64 位 arm64 / aarch64 |
| 内存 | 4GB 以上，推荐 6GB+ |
| 存储空间 | 至少 2GB 可用空间 |
| 网络 | WiFi 稳定连接 |

长期运行时建议关闭 Termux 的电池优化，否则手机息屏一段时间后后端可能被系统杀掉。

## 安装 Termux

从 F-Droid 安装 Termux：

```text
https://f-droid.org/packages/com.termux/
```

不要使用 Google Play 版 Termux，它已经长期不更新，很多包会安装失败。

首次打开 Termux 后执行：

```bash
pkg update -y
pkg upgrade -y
```

如果提示选择配置文件，直接回车使用默认值即可。

## 一键部署

在 Termux 中执行：

```bash
pkg install -y git
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
chmod +x scripts/*.sh
bash scripts/deploy-termux.sh
```

部署完成后打开手机浏览器：

```text
http://127.0.0.1:8080
```

同一 WiFi 下的电脑也可以访问，先查看手机 IP：

```bash
ip addr show wlan0 | grep inet
```

假设手机 IP 是 `192.168.1.100`，电脑访问：

```text
http://192.168.1.100:8080
```

## 一键脚本做了什么

`scripts/deploy-termux.sh` 会自动完成以下步骤：

1. 安装 Termux 软件包：`python`、`nodejs`、`git`、`nginx`、`curl`、编译依赖
2. 创建 Python 虚拟环境 `.venv`
3. 安装后端依赖 `backend/requirements.txt`
4. 复制 `backend/.env.example` 为 `backend/.env`
5. 安装前端依赖并执行 `npm run build`
6. 将 `frontend/dist` 复制到 `.termux-nginx/html`
7. 生成独立 Nginx 配置 `.termux-nginx/nginx.conf`
8. 后台启动 FastAPI 后端
9. 启动 Termux Nginx
10. 自动访问 `/api/health` 做健康检查

## 手动部署

如果一键脚本失败，可以按下面步骤手动执行。

### 安装基础软件

```bash
pkg update -y
pkg upgrade -y
pkg install -y python nodejs git nginx curl clang make openssl libffi
```

### 拉取代码

```bash
cd ~
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
```

### 安装后端

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
```

编辑配置：

```bash
nano backend/.env
```

关键项：

```env
SECRET_KEY=请改成一串随机字符串
DATABASE_URL=sqlite:///data/data.db
PLAYWRIGHT_HEADLESS=true
```

邮件通知需要 SMTP 配置，例如 QQ 邮箱：

```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your@qq.com
SMTP_PASSWORD=邮箱授权码
EMAIL_FROM=your@qq.com
```

### 构建前端

```bash
cd frontend
npm install
npm run build
```

构建成功后应看到：

```bash
ls dist/index.html
```

### 准备 Nginx 目录

```bash
cd ~/quan-zidong-zhushou
mkdir -p .termux-nginx/html .termux-nginx/logs .termux-nginx/tmp
cp -r frontend/dist/* .termux-nginx/html/
```

### 写入 Nginx 配置

```bash
cat > .termux-nginx/nginx.conf << 'EOF'
worker_processes  1;
error_log logs/error.log;
pid logs/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /data/data/com.termux/files/usr/etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log logs/access.log;
    sendfile on;
    keepalive_timeout 65;

    client_body_temp_path tmp/client_body;
    proxy_temp_path tmp/proxy;
    fastcgi_temp_path tmp/fastcgi;
    uwsgi_temp_path tmp/uwsgi;
    scgi_temp_path tmp/scgi;

    server {
        listen 8080;
        server_name 127.0.0.1 localhost;

        root html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 60s;
            proxy_connect_timeout 10s;
        }
    }
}
EOF
```

### 启动后端

```bash
cd ~/quan-zidong-zhushou
source .venv/bin/activate
cd backend
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > ../backend.log 2>&1 &
```

验证：

```bash
curl http://127.0.0.1:8000/api/health
```

期望返回：

```json
{"status":"healthy"}
```

### 启动 Nginx

```bash
cd ~/quan-zidong-zhushou
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/"
```

访问：

```text
http://127.0.0.1:8080
```

## 常用命令

查看后端日志：

```bash
tail -f ~/quan-zidong-zhushou/backend.log
```

查看 Nginx 日志：

```bash
tail -f ~/quan-zidong-zhushou/.termux-nginx/logs/error.log
tail -f ~/quan-zidong-zhushou/.termux-nginx/logs/access.log
```

停止后端：

```bash
pkill -f "uvicorn main:app"
```

停止 Nginx：

```bash
cd ~/quan-zidong-zhushou
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/" -s stop
```

重启全部服务：

```bash
cd ~/quan-zidong-zhushou
pkill -f "uvicorn main:app" 2>/dev/null || true
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/" -s stop 2>/dev/null || true
bash scripts/deploy-termux.sh
```

## 开机自启

安装 Termux:Boot：

```text
https://f-droid.org/packages/com.termux.boot/
```

打开 Termux:Boot 一次，然后在 Termux 中执行：

```bash
mkdir -p ~/.termux/boot

cat > ~/.termux/boot/start-auto-sign.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/quan-zidong-zhushou
pkill -f "uvicorn main:app" 2>/dev/null || true
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/" -s stop 2>/dev/null || true
source .venv/bin/activate
cd backend
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > ../backend.log 2>&1 &
cd ..
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/"
EOF

chmod +x ~/.termux/boot/start-auto-sign.sh
```

手机重启后，Termux:Boot 会自动启动后端和 Nginx。

## 后台保活

Android 可能会在息屏后停止 Termux 进程。建议设置：

1. 系统设置 → 应用 → Termux → 电池 → 不限制
2. 系统设置 → 应用 → Termux:Boot → 电池 → 不限制
3. Termux 中执行：

```bash
termux-wake-lock
```

如果长期运行，建议手机插电并连接稳定 WiFi。

## 更新项目

```bash
cd ~/quan-zidong-zhushou
git pull
bash scripts/deploy-termux.sh
```

脚本会重新构建前端、重启后端和 Nginx。

## 常见问题

### 页面能打开但登录失败

先确认 API 是否正常：

```bash
curl http://127.0.0.1:8080/api/health
```

如果 8080 下的 `/api/health` 失败，但 8000 成功，说明 Nginx 反向代理配置有问题：

```bash
curl http://127.0.0.1:8000/api/health
```

重新执行：

```bash
bash scripts/deploy-termux.sh
```

### 8080 端口被占用

查找占用进程：

```bash
ss -ltnp | grep 8080
```

停止 Nginx：

```bash
cd ~/quan-zidong-zhushou
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/" -s stop
```

如果仍然占用，可以把 `.termux-nginx/nginx.conf` 中的 `listen 8080;` 改成 `listen 8081;`。

### pip 安装失败

切换 Python 镜像源：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r backend/requirements.txt
```

### npm 安装失败

切换 npm 镜像源：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 手机浏览器能访问，电脑访问不了

确认手机和电脑在同一个 WiFi 下，然后查看手机 IP：

```bash
ip addr show wlan0 | grep inet
```

如果电脑仍然访问不了，检查手机系统是否限制局域网访问，或者把浏览器地址改成：

```text
http://手机IP:8080
```

### Playwright 在手机上不可用

纯 Termux 环境下不保证 Playwright Chromium 能在所有安卓设备上稳定运行。V1 的插件系统可以先用 Cookie、Token 或普通 HTTP 请求完成签到；需要复杂浏览器自动化时，更推荐部署到 Linux 服务器或 Docker。

## 部署完成后

打开：

```text
http://127.0.0.1:8080
```

然后按顺序完成：

1. 注册用户
2. 添加网站
3. 添加账号
4. 创建定时任务
5. 在日志页面查看签到结果

