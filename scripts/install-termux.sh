#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "更新 Termux 软件源..."
pkg update -y
pkg upgrade -y

echo "安装基础依赖..."
pkg install -y python nodejs git clang make openssl libffi

echo "准备 Python 虚拟环境..."
python -m venv "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"

python -m pip install --upgrade pip wheel setuptools
pip install -r "$BACKEND_DIR/requirements.txt"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi
mkdir -p "$BACKEND_DIR/data"

echo "安装前端依赖并构建静态文件..."
cd "$FRONTEND_DIR"
npm install
npm run build

echo "Termux 环境安装完成。"
echo "运行 scripts/start-termux.sh 启动 FastAPI 后端。"
echo "如果使用 WSToolbox，请把 frontend/dist 目录复制到 WSToolbox 的 Nginx 网站根目录。"
