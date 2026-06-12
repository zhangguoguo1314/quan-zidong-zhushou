# 阶段 1: 构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# 阶段 2: 构建后端镜像（无需 Playwright/Chrome，使用自定义 API 模式）
FROM python:3.11-slim

WORKDIR /app

# 安装最小依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 复制前端构建产物到 backend/static
COPY --from=frontend-builder /app/frontend/dist ./static

RUN mkdir -p /app/data

EXPOSE 8000

ENV DATABASE_URL=sqlite:///app/data/data.db
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
