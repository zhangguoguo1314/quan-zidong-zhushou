# Android 手机部署指南（WSToolbox + Termux）

将"全自动助手"部署到你的安卓手机上，24 小时开机自动签到。

## 为什么选择这个方案

- **WSToolbox**：手机端的 Nginx / PHP / MariaDB 集成环境，用来托管前端静态页面和做反向代理
- **Termux**：手机端的 Linux 终端，用来运行 Python FastAPI 后端
- 两个 App 在同一台手机上配合，手机浏览器访问 http://手机IP:8080 即可

```
手机浏览器 ──▶ WSToolbox(Nginx:8080) ──▶ 前端静态页面
                        │
                        └──▶ /api/* ──▶ Termux(Python:8000)
```

## 准备工作

### 手机要求

| 项目 | 要求 |
|------|------|
| 系统 | Android 7.0 及以上（推荐 Android 10+） |
| CPU | 64 位（arm64 / aarch64） |
| 内存 | 4GB 以上（推荐 6GB+） |
| 存储 | 2GB 可用空间 |
| 网络 | WiFi 稳定连接 |

### 需要安装的 App

1. **WSToolbox**（手机本地服务器）
   - 官网：https://wstoolbox.cn
   - 或从应用市场/GitHub 下载 APK 安装
2. **Termux**（Linux 终端）
   - 从 F-Droid 下载（推荐，持续更新）：https://f-droid.org/packages/com.termux/
   - **注意**：Google Play 版本已停止更新，不要用
3. **MT管理器** 或 **Files 谷歌文件**（方便复制文件）

---

## 第一部分：安装 Termux 并运行后端

### 步骤 1：打开 Termux，初始化环境

打开 Termux App，执行：

```bash
# 更新软件源
pkg update -y
pkg upgrade -y
# 如果有提示选择，直接回车选默认值
```

### 步骤 2：安装基础软件

```bash
pkg install -y python git clang make openssl libffi
```

验证：

```bash
python --version    # 期望 Python 3.11.x
```

### 步骤 3：获取项目代码

```bash
cd ~
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
```

> 如果 GitHub 访问慢，可以用镜像：
> ```
> git clone https://ghproxy.com/https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
> ```

### 步骤 4：一键安装后端依赖

```bash
chmod +x scripts/install-termux.sh
bash scripts/install-termux.sh
```

这个脚本会：

1. 创建 Python 虚拟环境 `.venv`
2. 安装 `backend/requirements.txt` 的所有 Python 依赖
3. 创建 `backend/.env` 配置文件
4. 安装前端 npm 依赖并构建静态文件到 `frontend/dist`

### 步骤 5：测试后端能否启动

```bash
bash scripts/start-termux.sh
```

看到类似输出表示成功：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

新开一个 Termux 会话（左滑屏幕 → 新建会话），验证：

```bash
curl http://127.0.0.1:8000/api/health
# 期望返回: {"status":"healthy"}
```

按 `Ctrl+C` 停止后端（我们先关掉它，后面用后台方式运行）。

---

## 第二部分：安装 WSToolbox 并托管前端

### 步骤 1：打开 WSToolbox，启动 Nginx

1. 打开 WSToolbox App
2. 在"服务"页面，开启 **Nginx**
3. 确认状态显示为"运行中"

### 步骤 2：复制前端静态文件到 WSToolbox 网站目录

WSToolbox 的网站根目录通常在：

- `/sdcard/WSToolbox/sites/`
- 或 `/storage/emulated/0/WSToolbox/sites/`

在 Termux 中执行：

```bash
# 先获取 storage 权限（首次需要）
termux-setup-storage
# 手机上会弹出权限请求，选"允许"

# 创建网站目录
mkdir -p /sdcard/WSToolbox/sites/quan-zidong-zhushou

# 复制前端静态文件
cp -r ~/quan-zidong-zhushou/frontend/dist/* /sdcard/WSToolbox/sites/quan-zidong-zhushou/

# 确认 index.html 存在
ls /sdcard/WSToolbox/sites/quan-zidong-zhushou/index.html
```

### 步骤 3：配置 WSToolbox 的 Nginx

在项目中已经准备好配置文件 `docs/wstoolbox-nginx.conf`，你需要：

**方法 A：在 WSToolbox App 中直接配置**

1. 打开 WSToolbox → 站点 → 新建站点（或叫"虚拟主机"/"网站"）
2. 站点名称：`quan-zidong-zhushou`
3. 根目录：`/sdcard/WSToolbox/sites/quan-zidong-zhushou`
4. 端口：`8080`（或你喜欢的端口）
5. 默认文档：`index.html`
6. URL 重写/反向代理：
   - 匹配路径：`/api/`
   - 目标地址：`http://127.0.0.1:8000/api/`
   - 类型：反向代理

**方法 B：手动编辑 Nginx 配置文件**

在 Termux 中：

```bash
# 找到 WSToolbox 的 Nginx 配置目录（通常在 /sdcard/WSToolbox/conf/nginx/ 下）
# 把我们的配置文件复制过去
cp ~/quan-zidong-zhushou/docs/wstoolbox-nginx.conf /sdcard/WSToolbox/conf/nginx/vhost/quan-zidong-zhushou.conf
```

然后在 WSToolbox App 中 → Nginx → 重新加载 / 重启

配置文件内容参考：

```nginx
server {
    listen 8080;
    server_name 127.0.0.1 localhost;

    root /sdcard/WSToolbox/sites/quan-zidong-zhushou;
    index index.html;

    # 前端页面路由（Vue Router 的 history 模式需要）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 请求转发到 Termux 中的 Python 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 步骤 4：验证前端

在手机浏览器访问：

```
http://127.0.0.1:8080
```

如果看到登录页面，说明前端已经正常工作。

---

## 第三部分：启动后端并让它后台运行

回到 Termux，我们用 `nohup` 让后端在后台运行：

```bash
cd ~/quan-zidong-zhushou

# 方式 A：nohup 简单后台运行
nohup bash scripts/start-termux.sh > backend.log 2>&1 &

# 方式 B：用 screen 会话管理（推荐）
pkg install -y screen
screen -S backend
# 在新 screen 窗口中运行
bash scripts/start-termux.sh
# 按 Ctrl+A 然后按 D 退出会话（后端继续在后台运行）
# 需要看日志时运行: screen -r backend
```

验证后端在运行：

```bash
curl http://127.0.0.1:8000/api/health
# 返回: {"status":"healthy"}
```

查看日志：

```bash
cd ~/quan-zidong-zhushou
tail -f backend.log
```

---

## 第四部分：一键部署脚本（省事版）

如果前面的步骤你嫌麻烦，直接在 Termux 中运行这个一键脚本：

```bash
cd ~
git clone https://github.com/zhangguoguo1314/quan-zidong-zhushou.git
cd quan-zidong-zhushou
chmod +x scripts/deploy-wstoolbox.sh
bash scripts/deploy-wstoolbox.sh
```

脚本会自动：

1. 安装 Termux 需要的软件包
2. 安装 Python 依赖
3. 安装前端依赖并构建静态文件
4. 将前端文件复制到 WSToolbox 网站目录
5. 将 Nginx 配置文件复制到 WSToolbox 配置目录
6. 在后台启动 Python 后端

脚本执行完成后：

- 在手机浏览器打开 http://127.0.0.1:8080
- 注册账号 → 登录 → 使用

---

## 第五部分：手机 IP 地址，从其他设备访问

查看手机在局域网内的 IP 地址：

```bash
# Termux 中
ip addr show wlan0 | grep inet
# 或者
ifconfig wlan0
```

假设手机 IP 是 `192.168.1.100`，那么：

- 手机上访问：http://127.0.0.1:8080
- 同局域网电脑访问：http://192.168.1.100:8080

> 需要注意：WSToolbox 的 Nginx 默认可能只监听本地。如果外网访问不了，检查 Nginx 配置中 `listen` 是否是 `0.0.0.0:8080` 而不是 `127.0.0.1:8080`。

---

## 第六部分：开机自启（可选）

### 用 Termux:Boot 实现开机自动运行

1. 从 F-Droid 安装 **Termux:Boot**：https://f-droid.org/packages/com.termux.boot/
2. 打开 Termux:Boot 一次（授予权限）
3. 在 Termux 中：

```bash
mkdir -p ~/.termux/boot

cat > ~/.termux/boot/start-auto-sign.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/quan-zidong-zhushou
nohup bash scripts/start-termux.sh > backend.log 2>&1 &
EOF

chmod +x ~/.termux/boot/start-auto-sign.sh
```

下次手机重启后，Termux 会自动启动并运行后端。

---

## 常见问题

### Q1：WSToolbox 的 Nginx 启动后，访问 8080 报 404

**原因**：前端文件路径配置错误，或 index.html 不存在。

**排查**：

```bash
ls /sdcard/WSToolbox/sites/quan-zidong-zhushou/index.html
# 应该能看到 index.html
```

如果没有文件，重新执行：

```bash
cd ~/quan-zidong-zhushou/frontend
npm install
npm run build
cp -r dist/* /sdcard/WSToolbox/sites/quan-zidong-zhushou/
```

### Q2：/api 请求返回 502 Bad Gateway

**原因**：后端 Python 服务没启动，或者端口配置不一致。

**排查**：

```bash
# 确认后端在运行
curl http://127.0.0.1:8000/api/health
# 应该返回 {"status":"healthy"}
```

如果连不上，重新启动后端：

```bash
cd ~/quan-zidong-zhushou
bash scripts/start-termux.sh
```

### Q3：npm install 在 Termux 中特别慢或失败

**解决**：设置国内镜像源：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q4：pip install 失败

**解决**：使用清华镜像源：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r backend/requirements.txt
```

### Q5：手机休眠后后端停止运行

**原因**：Android 的电池优化策略在手机休眠时会杀死后台进程。

**解决**：

1. 系统设置 → 电池 → 电池优化 → 找到 Termux → 选择"不优化"
2. 系统设置 → WSToolbox → 同样选择"不优化"
3. 在 Termux 中运行：`termux-wake-lock`（防止 CPU 休眠）

### Q6：Playwright 在手机上无法安装浏览器

**原因**：Playwright 的 Chromium 不一定支持所有 ARM 安卓设备。

**解决**：V1 的签到任务可以先不用 Playwright。如果必须用，可以：

1. 直接安装 `chromium` 包：`pkg install -y chromium`
2. 或者改用 `requests` + `BeautifulSoup` 方式实现签到（更轻量，适合手机）
3. 目前 V1 的插件系统支持自定义签到脚本，不需要 Playwright 也可以工作

### Q7：如何升级项目代码

```bash
cd ~/quan-zidong-zhushou

# 停止后端
pkill -f uvicorn

# 拉取最新代码
git pull

# 重新安装依赖（如果 requirements.txt 或 package.json 有变化）
bash scripts/install-termux.sh

# 复制新的前端文件
cp -r frontend/dist/* /sdcard/WSToolbox/sites/quan-zidong-zhushou/

# 重启后端
nohup bash scripts/start-termux.sh > backend.log 2>&1 &
```

---

## 端口参考

| 组件 | 端口 | 说明 |
|------|------|------|
| WSToolbox Nginx（前端） | 8080 | 手机浏览器直接访问 |
| Termux Python 后端 | 8000 | 只在本机/局域网可访问，不对外暴露 |
| API 反向代理路径 | /api/* | 由 Nginx 转发到后端 |

## 部署成功后的使用

1. 手机浏览器打开 http://127.0.0.1:8080
2. 注册账号 → 登录
3. 添加网站 → 添加账号 → 设置定时任务
4. 系统会按照你设置的时间自动执行签到
5. 签到结果可以在"日志"页面查看
