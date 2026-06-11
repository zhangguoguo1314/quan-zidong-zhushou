#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# 全自动助手 - 纯 Termux 一键部署脚本
# 不依赖 WSToolbox：Termux 同时运行 FastAPI 后端和 Nginx 前端服务。

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
NGINX_DIR="$ROOT_DIR/.termux-nginx"
NGINX_HTML="$NGINX_DIR/html"
NGINX_CONF="$NGINX_DIR/nginx.conf"
BACKEND_LOG="$ROOT_DIR/backend.log"

echo "======================================================"
echo "  全自动助手 - 纯 Termux 一键部署"
echo "======================================================"
echo ""

if [ ! -d "/data/data/com.termux" ]; then
  echo "此脚本必须在 Termux 中运行。"
  exit 1
fi

echo "[1/8] 安装基础软件包..."
pkg update -y
pkg upgrade -y
pkg install -y python nodejs git nginx curl clang make openssl libffi

echo ""
echo "[2/8] 创建 Python 虚拟环境并安装后端依赖..."
cd "$ROOT_DIR"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source "$ROOT_DIR/.venv/bin/activate"
python -m pip install --upgrade pip wheel setuptools
pip install -r "$BACKEND_DIR/requirements.txt"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

echo ""
echo "[3/8] 安装前端依赖并构建静态文件..."
cd "$FRONTEND_DIR"
npm install
npm run build

echo ""
echo "[4/8] 准备 Nginx 目录..."
mkdir -p "$NGINX_HTML" "$NGINX_DIR/logs" "$NGINX_DIR/tmp/client_body" "$NGINX_DIR/tmp/proxy" "$NGINX_DIR/tmp/fastcgi" "$NGINX_DIR/tmp/uwsgi" "$NGINX_DIR/tmp/scgi"
rm -rf "$NGINX_HTML"/*
cp -r "$FRONTEND_DIR/dist/"* "$NGINX_HTML/"

echo ""
echo "[5/8] 生成 Nginx 配置..."
cat > "$NGINX_CONF" <<EOF
worker_processes  1;
error_log logs/error.log;
pid logs/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include $PREFIX/etc/nginx/mime.types;
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
            try_files \$uri \$uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:8000/api/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 60s;
            proxy_connect_timeout 10s;
        }
    }
}
EOF

echo ""
echo "[6/8] 停止旧服务..."
pkill -f "uvicorn main:app" 2>/dev/null || true
nginx -c "$NGINX_CONF" -p "$NGINX_DIR/" -s stop 2>/dev/null || true
sleep 1

echo ""
echo "[7/8] 启动 FastAPI 后端..."
source "$ROOT_DIR/.venv/bin/activate"
cd "$BACKEND_DIR"
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"
sleep 3

echo ""
echo "[8/8] 启动 Termux Nginx..."
cd "$ROOT_DIR"
nginx -c "$NGINX_CONF" -p "$NGINX_DIR/"
sleep 1

echo ""
echo "======================================================"
echo "  验证服务"
echo "======================================================"

if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
  echo "后端 FastAPI: OK"
else
  echo "后端 FastAPI: 异常，请查看日志：tail -f $BACKEND_LOG"
fi

if curl -s http://127.0.0.1:8080/api/health | grep -q "healthy"; then
  echo "Nginx 反向代理: OK"
else
  echo "Nginx 反向代理: 异常，请查看日志：tail -f $NGINX_DIR/logs/error.log"
fi

if [ -f "$NGINX_HTML/index.html" ]; then
  echo "前端静态文件: OK"
else
  echo "前端静态文件: 异常，未找到 index.html"
fi

PHONE_IP="$(ip addr show wlan0 2>/dev/null | grep -oP 'inet \K[0-9.]+' | head -1 || true)"

echo ""
echo "======================================================"
echo "  部署完成"
echo "======================================================"
echo "手机访问: http://127.0.0.1:8080"
if [ -n "$PHONE_IP" ]; then
  echo "同 WiFi 设备访问: http://$PHONE_IP:8080"
fi
echo ""
echo "常用命令："
echo "查看后端日志: tail -f $BACKEND_LOG"
echo "查看 Nginx 日志: tail -f $NGINX_DIR/logs/error.log"
echo "停止后端: pkill -f 'uvicorn main:app'"
echo "停止 Nginx: nginx -c \"$NGINX_CONF\" -p \"$NGINX_DIR/\" -s stop"
echo ""
