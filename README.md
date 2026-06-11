# Account-Auto-Sign V1

多网站多账号自动签到平台

## 简介

Account-Auto-Sign 是一个支持多网站、多账号自动签到的平台，帮助用户自动化日常签到任务。

## 技术栈

- **后端**: Python 3.11 + FastAPI + SQLAlchemy + APScheduler + Playwright
- **前端**: Vue 3 + TypeScript + Element Plus + Pinia + Vue Router
- **数据库**: SQLite
- **部署**: Docker / Docker Compose

## 功能特性

- ✅ 用户系统（注册/登录/JWT认证）
- ✅ 网站管理（CRUD）
- ✅ 账号管理（CRUD、CSV导入、批量添加）
- ✅ 定时任务（Cron 调度）
- ✅ 签到日志（查看、筛选、删除）
- ✅ 邮件通知（失败时发送邮件）
- ✅ Playwright 自动化签到（支持多种网站类型）
- ✅ 插件系统（支持自定义签到逻辑
- ✅ Docker 部署

## 项目结构

```
account-auto-sign/
├── backend/          # Python FastAPI 后端
│   ├── api/       # API 路由
│   ├── models/    # SQLAlchemy 模型
│   ├── schemas/   # Pydantic schemas
│   ├── services/  # 业务逻辑服务
│   ├── plugins/   # 签到插件系统
│   ├── tasks/     # 任务调度
│   └── core/      # 核心模块(配置/数据库/安全)
├── frontend/        # Vue3 + TypeScript 前端
│   └── src/
│       ├── pages/  # 页面组件
│       ├── stores/ # Pinia 状态管理
│       ├── api/    # API 客户端
│       └── router/ # Vue Router
├── Dockerfile     # 后端 Docker
├── docker-compose.yml # Compose 配置
└── README.md
```

## 快速开始

### 方式一：Docker（推荐）

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd account-auto-sign-v1

# 2. 一键启动
docker-compose up --build
```

### 方式二：本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 访问地址

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## API 路由
## 配置

编辑 `backend/.env.example` 为 `.env` 以配置邮件通知：

```env
# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@example.com
```

## 许可证

MIT License
