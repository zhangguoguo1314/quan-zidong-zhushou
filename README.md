# 全自动签到助手

> 一站式多站点自动签到管理系统，支持自定义 API 签到、邮件/企业微信通知、定时任务调度。

## 功能特性

- **多站点管理** — 支持自定义添加站点，内置常用站点预设（荔枝鱼、哈基米API、binmt论坛等）
- **自定义分类** — 站点按分类分组管理，支持自定义添加/删除分类
- **自动签到** — 基于 APScheduler 定时任务调度，支持 Cron 表达式自定义频率
- **通用签到引擎** — 支持登录→提取Token→签到完整流程，兼容 JSON/Form/Cookie 多种认证方式
- **Cookie 心跳** — 自动刷新登录 Cookie，防止会话过期
- **消息通知** — 邮件 + 企业微信机器人通知，支持自定义消息模板
- **定时状态报告** — 自定义间隔发送系统运行状态摘要
- **AI 配置生成** — 输入网站地址自动探测 API 接口，生成可导入的配置
- **多语言** — 支持中文/English/日本語 切换
- **响应式设计** — 手机/平板/桌面全适配
- **日志管理** — 签到日志查看、详情、CSV 导出

## 技术栈

### 后端
- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- APScheduler 定时调度
- httpx 异步 HTTP 客户端
- python-jose JWT 认证
- aiosmtplib 邮件发送

### 前端
- Vue 3 + TypeScript
- Pinia 状态管理
- Element Plus UI 组件库
- Vue Router
- Vite 构建
- TailwindCSS

## 快速开始

### 本地部署

```bash
# 1. 克隆仓库
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 启动后端
uvicorn main:app --host 0.0.0.0 --port 8000

# 4. 安装前端依赖（开发模式）
cd ../frontend
npm install
npm run dev
```

访问 http://localhost:8000（生产模式，前端已内置到 static 目录）
或 http://localhost:5173（开发模式，热更新）

### Docker 部署

```bash
docker build -t auto-signin .
docker run -d -p 7860:7860 auto-signin
```

### Hugging Face Spaces 部署

项目已适配 Hugging Face Spaces，直接推送到仓库即可自动部署。

## 内置站点预设

| 站点 | 分类 | 认证方式 |
|------|------|----------|
| 荔枝鱼公益站 | 公益站点 | Bearer Token |
| 哈基米API站 | API服务 | Session Cookie + Header |
| binmt论坛 | 论坛社区 | Discuz Cookie |

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/health | GET | 健康检查 |
| /api/auth/register | POST | 用户注册 |
| /api/auth/login | POST | 用户登录 |
| /api/auth/me | GET | 获取当前用户 |
| /api/sites | GET/POST | 站点列表/创建 |
| /api/sites/categories | GET/POST | 分类管理 |
| /api/sites/grouped | GET | 按分类分组 |
| /api/accounts | GET/POST | 账号管理 |
| /api/tasks | GET/POST | 任务管理 |
| /api/tasks/{id}/run | POST | 手动执行任务 |
| /api/logs | GET | 签到日志 |
| /api/logs/export | GET | 导出日志 CSV |
| /api/logs/{id} | GET | 日志详情 |
| /api/settings | GET/PUT | 系统设置 |
| /api/settings/templates/defaults | GET | 默认消息模板 |
| /api/settings/templates/preview | POST | 模板预览 |
| /api/settings/send-status-report | POST | 发送状态报告 |
| /api/config-generator/probe | POST | AI 探测站点配置 |

## 消息模板变量

签到通知支持以下占位符变量：

| 变量 | 说明 |
|------|------|
| {site_name} | 站点名称 |
| {account_name} | 账号名称 |
| {status} | 签到状态 |
| {message} | 签到消息 |
| {time} | 当前时间 |
| {error} | 错误信息 |
| {success_count} | 成功次数 |
| {fail_count} | 失败次数 |
| {total_sites} | 总站点数 |
| {total_accounts} | 总账号数 |

## 项目结构

```
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 配置、安全、数据库
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic Schema
│   ├── api/routes/          # API 路由
│   ├── services/            # 业务服务
│   │   ├── signin_executor.py   # 签到执行引擎
│   │   ├── config_generator.py  # AI 配置生成器
│   │   ├── notification.py      # 通知服务
│   │   ├── wechat_bot.py        # 企业微信机器人
│   │   └── message_template.py  # 消息模板引擎
│   ├── tasks/               # 定时任务
│   │   └── scheduler.py     # APScheduler 调度器
│   └── static/              # 前端构建产物
├── frontend/
│   ├── src/
│   │   ├── pages/           # 页面组件
│   │   ├── stores/          # Pinia Store
│   │   ├── api/             # API 封装
│   │   ├── i18n/            # 国际化
│   │   └── router/          # 路由配置
│   └── vite.config.ts
├── Dockerfile
└── README.md
```

## License

MIT
