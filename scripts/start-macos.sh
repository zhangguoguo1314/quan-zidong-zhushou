#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "✗ 未找到 .venv，请先运行 scripts/install-macos.sh"
  exit 1
fi

echo "======================================================"
echo "  全自动助手 - 启动服务"
echo "======================================================"
echo ""

cd "$ROOT_DIR"

# 启动后端（后台运行）
source .venv/bin/activate
cd "$ROOT_DIR/backend"
echo "→ 启动后端 FastAPI (端口 8000)"
uvicorn main:app --host 127.0.0.1 --port 8000 > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID"

# 启动前端
cd "$ROOT_DIR/frontend"
echo "→ 启动前端 Vite (端口 5173)"
echo ""
echo "  访问地址："
echo "    前端: http://localhost:5173"
echo "    后端: http://localhost:8000"
echo "    文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo ""

# 捕获 Ctrl+C，清理后端进程
trap "kill $BACKEND_PID 2>/dev/null; echo ''; echo '→ 正在停止服务...'; exit 0" INT TERM

npm run dev

# 如果 npm run dev 退出，也清理后端
kill $BACKEND_PID 2>/dev/null || true
