#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "未找到 .venv，请先运行 scripts/install-termux.sh。"
  exit 1
fi

source "$ROOT_DIR/.venv/bin/activate"

cd "$ROOT_DIR/backend"
echo "启动 FastAPI 后端：http://127.0.0.1:8000"
uvicorn main:app --host 0.0.0.0 --port 8000
