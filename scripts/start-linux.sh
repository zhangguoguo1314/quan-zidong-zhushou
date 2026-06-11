#!/usr/bin/env bash
set -euo pipefail

# 全自动助手 - Linux 启动脚本
# 同时启动 FastAPI 后端和 Vite 前端

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "✗ 未找到 .venv，请先运行 scripts/install-linux.sh"
  exit 1
fi

echo "======================================================"
echo "  全自动助手 - 启动服务"
echo "======================================================"
echo ""

# 激活虚拟环境
source "$ROOT_DIR/.venv/bin/activate"

# 启动后端（后台运行）
echo "→ 启动后端 FastAPI (端口 8000)"
cd "$BACKEND_DIR"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "  后端 PID: $BACKEND_PID (日志: backend.log)"

# 等待后端就绪
sleep 2

# 检查后端是否启动成功
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
  echo "  后端: OK"
else
  echo "  后端: 启动中或异常，请查看日志: tail -f $LOG_DIR/backend.log"
fi

echo ""
echo "→ 启动前端 Vite (端口 5173)"
echo ""
echo "  访问地址："
echo "    前端: http://localhost:5173"
echo "    后端: http://localhost:8000"
echo "    文档: http://localhost:8000/docs"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo ""

cd "$FRONTEND_DIR"

# 捕获 Ctrl+C 清理
cleanup() {
  echo ""
  echo "→ 正在停止服务..."
  kill $BACKEND_PID 2>/dev/null || true
  wait $BACKEND_PID 2>/dev/null || true
  echo "服务已停止"
  exit 0
}
trap cleanup INT TERM

# 前台运行前端（npm run dev
npm run dev
