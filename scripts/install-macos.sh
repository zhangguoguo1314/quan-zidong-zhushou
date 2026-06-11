#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "======================================================"
echo "  全自动助手 - macOS 一键安装脚本"
echo "======================================================"
echo ""

echo "正在检查运行环境..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "✗ 未找到 python3，请先安装 Python 3.11+"
  echo "  推荐: brew install python@3.11"
  exit 1
fi

# 验证 Python 版本 >= 3.11
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
if ! python3 -c "import sys; sys.exit(0 if (sys.version_info.major==3 and sys.version_info.minor>=11) else 1)" 2>/dev/null; then
  echo "✗ Python 版本 $PYVER 过低，需要 Python 3.11 或更高"
  echo "  推荐: brew install python@3.11"
  exit 1
fi
echo "✓ Python $PYVER"

if ! command -v node >/dev/null 2>&1; then
  echo "✗ 未找到 node，请先安装 Node.js 20+"
  echo "  推荐: brew install node@20"
  exit 1
fi
echo "✓ Node.js $(node --version)"

if ! command -v npm >/dev/null 2>&1; then
  echo "✗ 未找到 npm，请先安装 Node.js（会自带 npm"
  exit 1
fi
echo "✓ npm $(npm --version)"

echo ""
echo "======================================================"
echo "  第 1 步：创建 Python 虚拟环境"
echo "======================================================"

cd "$ROOT_DIR"
python3 -m venv .venv
source .venv/bin/activate
echo "✓ 虚拟环境已创建"

echo ""
echo "======================================================"
echo "  第 2 步：安装后端 Python 依赖"
echo "======================================================"

python -m pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
echo "✓ Python 依赖安装完成"

echo ""
echo "======================================================"
echo "  第 3 步：安装 Playwright 浏览器内核（可选）"
echo "======================================================"

if pip list 2>/dev/null | grep -q playwright >/dev/null 2>&1; then
  echo "正在安装 Playwright Chromium 浏览器..."
  npx --yes playwright install chromium 2>/dev/null || playwright install chromium || echo "  (浏览器安装跳过，可稍后手动运行: playwright install chromium)"
fi

echo ""
echo "======================================================"
echo "  第 4 步：创建后端配置文件"
echo "======================================================"

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "✓ 已复制 .env.example -> .env"
else
  echo "✓ .env 已存在，跳过"
fi

echo ""
echo "======================================================"
echo "  第 5 步：安装前端依赖并构建"
echo "======================================================"

cd "$FRONTEND_DIR"
npm install
npm run build
echo "✓ 前端构建完成"

echo ""
echo "======================================================"
echo "  安装完成！"
echo "======================================================"
echo ""
echo "启动服务："
echo "  bash scripts/start-macos.sh"
echo ""
echo "访问地址："
echo "  前端: http://localhost:5173 (开发模式)"
echo "  前端: http://localhost:4173 (生产预览)"
echo "  后端: http://localhost:8000"
echo "  文档: http://localhost:8000/docs"
echo ""
