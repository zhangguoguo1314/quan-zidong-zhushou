#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# 全自动助手 - Android 手机一键部署脚本
# 在 Termux 中运行
# 使用方法:
#   cd ~/quan-zidong-zhushou
#   bash scripts/deploy-wstoolbox.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
WST_SITE="/sdcard/WSToolbox/sites/quan-zidong-zhushou"
WST_CONF_DIR="/sdcard/WSToolbox/conf/nginx/vhost"

echo "======================================================"
echo "  全自动助手 - Android 手机一键部署"
echo "  环境: Termux + WSToolbox"
echo "======================================================"
echo ""

# 检查是否在 Termux 中
if [ ! -d "/data/data/com.termux" ]; then
  echo "✗ 此脚本必须在 Termux 中运行"
  echo "  请安装 Termux: https://f-droid.org/packages/com.termux/"
  exit 1
fi

# 步骤 1: 请求存储权限
echo "[1/7] 检查存储权限..."
if [ ! -d "/sdcard" ]; then
  echo "  请求存储权限..."
  termux-setup-storage
  sleep 2
fi
if [ -d "/sdcard" ]; then
  echo "  OK"
else
  echo "  警告: 无法访问 /sdcard，请在系统设置中手动授予存储权限"
fi

# 步骤 2: 更新软件源并安装基础包
echo ""
echo "[2/7] 安装基础软件包 (python, git, nodejs)..."
pkg update -y
pkg upgrade -y
pkg install -y python nodejs git clang make openssl libffi
echo "  OK"

# 步骤 3: 安装 Python 虚拟环境和依赖
echo ""
echo "[3/7] 安装 Python 后端依赖..."
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
pip install -r "$BACKEND_DIR/requirements.txt"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi
echo "  OK"

# 步骤 4: 安装前端依赖并构建
echo ""
echo "[4/7] 构建前端静态文件..."
cd "$FRONTEND_DIR"
npm install
npm run build
echo "  OK"

# 步骤 5: 复制前端文件到 WSToolbox 网站目录
echo ""
echo "[5/7] 部署前端文件到 WSToolbox..."
mkdir -p "$WST_SITE"
cp -r "$FRONTEND_DIR/dist/"* "$WST_SITE/"
echo "  OK -> $WST_SITE"
echo "  首页: $WST_SITE/index.html"

# 步骤 6: 生成并复制 Nginx 配置文件
echo ""
echo "[6/7] 生成 Nginx 反向代理配置..."
mkdir -p "$WST_CONF_DIR"

cat > "$WST_CONF_DIR/quan-zidong-zhushou.conf" << 'NGINX'
server {
    listen 8080;
    server_name 127.0.0.1 localhost;

    root /sdcard/WSToolbox/sites/quan-zidong-zhushou;
    index index.html;

    client_max_body_size 10M;

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
NGINX

echo "  OK -> $WST_CONF_DIR/quan-zidong-zhushou.conf"
echo "  请在 WSToolbox App 中重启 Nginx 加载配置"

# 步骤 7: 启动后端
echo ""
echo "[7/7] 在后台启动 Python 后端..."
cd "$ROOT_DIR"
# 杀死已有的后端进程
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

source .venv/bin/activate
cd "$BACKEND_DIR"

# 用 nohup 后台运行
LOG_FILE="$ROOT_DIR/backend.log"
nohup uvicorn main:app --host 127.0.0.1 --port 8000 > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"
echo "  日志文件: $LOG_FILE"

# 等待后端启动
sleep 3

# 验证后端
echo ""
echo "======================================================"
echo "  验证部署..."
echo "======================================================"
echo ""

if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
  echo "  后端 FastAPI: OK"
else
  echo "  后端 FastAPI: 异常 (请检查日志: tail -f $LOG_FILE"
fi

if [ -f "$WST_SITE/index.html" ]; then
  echo "  前端静态文件:  OK"
else
  echo "  前端静态文件:  未找到"
fi

echo ""
echo "======================================================"
echo "  部署完成！"
echo "======================================================"
echo ""
echo "下一步操作："
echo "  1. 打开 WSToolbox App → 重启 Nginx"
echo "  2. 手机浏览器访问: http://127.0.0.1:8080"
echo "  3. 注册账号 → 登录 → 使用"
echo ""
echo "其他设备同局域网访问: http://$(ip addr show wlan0 2>/dev/null | grep -oP 'inet \K[0-9.]+' | head -1):8080"
echo ""
echo "常用命令："
echo "  查看后端日志: tail -f $LOG_FILE"
echo "  停止后端:     pkill -f uvicorn"
echo "  重启后端:     cd $ROOT_DIR && bash scripts/start-termux.sh"
echo ""
