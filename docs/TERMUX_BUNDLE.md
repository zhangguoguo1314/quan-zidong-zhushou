# Termux 一键启动包使用说明

这个包是为“手机上尽量少折腾”准备的。它已经包含构建好的前端文件，手机上不需要安装 Node.js，也不需要执行 `npm install` 或 `npm run build`。

## 这个包解决什么问题

普通源码部署需要在手机上安装 Python、Node.js、Nginx，还要编译前端。很多手机会卡在 Node 依赖、网络超时、内存不足或 npm 镜像问题上。

一键启动包把前端提前构建好，手机只做三件事：

1. 安装 Termux 里的 Python 和 Nginx
2. 安装后端 Python 依赖
3. 启动 FastAPI 后端和 Nginx 前端

## 手机需要准备

只需要安装 Termux：

```text
https://f-droid.org/packages/com.termux/
```

不要使用 Google Play 里的旧版 Termux。

## 使用方法

把 `quan-zidong-zhushou-termux-bundle.tar.gz` 放到手机，例如 `Download` 目录。

打开 Termux：

```bash
termux-setup-storage
cd ~/storage/downloads
tar -xzf quan-zidong-zhushou-termux-bundle.tar.gz
cd quan-zidong-zhushou
bash scripts/termux-oneclick.sh
```

启动完成后，手机浏览器打开：

```text
http://127.0.0.1:8080
```

如果电脑和手机在同一个 WiFi 下，也可以用手机 IP 访问：

```bash
ip addr show wlan0 | grep inet
```

例如手机 IP 是 `192.168.1.100`，电脑访问：

```text
http://192.168.1.100:8080
```

## 目录结构

```text
quan-zidong-zhushou/
├── backend/                 # FastAPI 后端
├── frontend/dist/           # 已构建好的前端页面
├── scripts/termux-oneclick.sh
├── docs/
└── README.md
```

## 常用命令

查看后端日志：

```bash
tail -f backend.log
```

停止后端：

```bash
pkill -f "uvicorn main:app"
```

停止 Nginx：

```bash
nginx -c "$PWD/.termux-nginx/nginx.conf" -p "$PWD/.termux-nginx/" -s stop
```

重新启动：

```bash
bash scripts/termux-oneclick.sh
```

## 常见问题

### 提示找不到 frontend/dist/index.html

你解压的不是一键启动包，可能是普通源码包。请使用文件名包含 `termux-bundle` 的压缩包。

### pip 安装失败

脚本已经内置清华镜像源重试。如果仍失败，先运行：

```bash
pkg update -y
pkg upgrade -y
```

然后重新执行：

```bash
bash scripts/termux-oneclick.sh
```

### 页面能打开但登录失败

检查 API：

```bash
curl http://127.0.0.1:8080/api/health
```

如果失败，看 Nginx 日志：

```bash
tail -f .termux-nginx/logs/error.log
```

### 手机息屏后停止运行

Android 会杀后台。建议：

1. 系统设置里把 Termux 电池策略改为“不限制”
2. Termux 中执行：

```bash
termux-wake-lock
```

## 关于 Playwright

纯手机 Termux 不保证 Playwright Chromium 能稳定运行。当前一键包保证基础 Web 管理平台能运行：注册、登录、添加网站、添加账号、任务管理、日志查看。

如果要做复杂浏览器自动化签到，建议放到 Linux 服务器或 Docker 环境。手机上更推荐先做 Cookie/Token/HTTP 请求型签到插件。
