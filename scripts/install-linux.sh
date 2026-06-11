#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "正在检查运行环境..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3，请先安装 Python 3.11 或更高版本。"
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "未找到 node，请先安装 Node.js 20 或更高版本。"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "未找到 npm，请先安装 npm。"
  exit 1
fi

echo "创建 Python 虚拟环境..."
python3 -m venv "$ROOT_DIR/.venv"
source "$ROOT_DIR/.venv/bin/activate"

echo "安装后端依赖..."
python -m pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

if command -v playwright >/dev/null 2>&1; then
  echo "安装 Playwright Chromium 浏览器..."
  playwright install chromium || true
fi

if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "创建后端 .env 配置..."
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

echo "安装前端依赖..."
cd "$FRONTEND_DIR"
npm install

echo "构建前端..."
npm run build

echo "安装完成。运行 scripts/start-linux.sh 启动服务。"
