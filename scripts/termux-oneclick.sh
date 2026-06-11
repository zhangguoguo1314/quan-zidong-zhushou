#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# 全自动助手 - Termux 一键启动脚本
# 用法：解压打包文件后，在项目根目录执行 bash scripts/termux-oneclick.sh
# 这个脚本使用包内已经构建好的 frontend/dist，手机上不再执行 npm install / npm run build。

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
DIST_DIR="$ROOT_DIR/frontend/dist"
NGINX_DIR="$ROOT_DIR/.termux-nginx"
NGINX_HTML="$NGINX_DIR/html"
NGINX_CONF="$NGINX_DIR/nginx.conf"
BACKEND_LOG="$ROOT_DIR/backend.log"

echo "======================================================"
echo "  全自动助手 - Termux 一键启动"
echo "======================================================"
echo ""

if [ ! -d "/data/data/com.termux" ]; then
  echo "此脚本必须在 Android 的 Termux 中运行。"
  exit 1
fi

if [ ! -f "$DIST_DIR/index.html" ]; then
  echo "未找到预构建前端：$DIST_DIR/index.html"
  echo "请确认你解压的是 termux-bundle 包，而不是普通源码包。"
  exit 1
fi

echo "[1/7] 安装运行环境..."
pkg update -y
pkg install -y python nginx curl clang make openssl libffi

echo ""
echo "[2/7] 创建 Python 虚拟环境..."
cd "$ROOT_DIR"
if [ -d ".venv" ] && [ ! -f ".venv/bin/activate" ]; then
  echo "检测到损坏的 .venv，正在删除并重新创建..."
  rm -rf .venv
fi
if [ ! -f ".venv/bin/activate" ]; then
  python -m venv .venv
fi
source "$ROOT_DIR/.venv/bin/activate"

echo ""
echo "[3/7] 安装后端依赖..."
python -m pip install --upgrade pip wheel setuptools
pip install -r "$BACKEND_DIR/requirements.txt" || pip install -r "$BACKEND_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi
mkdir -p "$BACKEND_DIR/data"

echo ""
echo "[4/7] 准备 Nginx 前端目录..."
mkdir -p "$NGINX_HTML" "$NGINX_DIR/logs" "$NGINX_DIR/tmp/client_body" "$NGINX_DIR/tmp/proxy" "$NGINX_DIR/tmp/fastcgi" "$NGINX_DIR/tmp/uwsgi" "$NGINX_DIR/tmp/scgi"
rm -rf "$NGINX_HTML"/*
cp -r "$DIST_DIR/"* "$NGINX_HTML/"

echo ""
echo "[5/7] 写入 Nginx 配置..."
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
echo "[6/7] 重启旧服务..."
pkill -f "uvicorn main:app" 2>/dev/null || true
nginx -c "$NGINX_CONF" -p "$NGINX_DIR/" -s stop 2>/dev/null || true
sleep 1

echo ""
echo "[7/7] 启动服务..."
source "$ROOT_DIR/.venv/bin/activate"
cd "$BACKEND_DIR"
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
sleep 3

cd "$ROOT_DIR"
nginx -c "$NGINX_CONF" -p "$NGINX_DIR/"
sleep 1

echo ""
echo "======================================================"
echo "  启动结果"
echo "======================================================"

if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
  echo "后端：正常"
else
  echo "后端：异常，请查看日志：tail -f $BACKEND_LOG"
fi

if curl -s http://127.0.0.1:8080/api/health | grep -q "healthy"; then
  echo "前端代理：正常"
else
  echo "前端代理：异常，请查看日志：tail -f $NGINX_DIR/logs/error.log"
fi

PHONE_IP="$(ip addr show wlan0 2>/dev/null | grep -oP 'inet \K[0-9.]+' | head -1 || true)"

echo ""
echo "手机浏览器访问：http://127.0.0.1:8080"
if [ -n "$PHONE_IP" ]; then
  echo "同 WiFi 设备访问：http://$PHONE_IP:8080"
fi
echo ""
echo "查看后端日志：tail -f $BACKEND_LOG"
echo "停止后端：pkill -f 'uvicorn main:app'"
echo "停止 Nginx：nginx -c \"$NGINX_CONF\" -p \"$NGINX_DIR/\" -s stop"
echo ""
