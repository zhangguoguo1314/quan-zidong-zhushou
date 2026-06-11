# 全自动助手 - Windows 一键安装脚本
# 使用方法: powershell -ExecutionPolicy Bypass -File scripts\install-windows.ps1

$ErrorActionPreference = "Stop"

# 获取项目根目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvDir = Join-Path $RootDir ".venv"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  全自动助手 - Windows 一键安装" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "正在检查 Python..."
try {
    $pyVersion = python --version 2>&1
    Write-Host "OK  $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "未找到 Python，请先安装 Python 3.11+" -ForegroundColor Red
    Write-Host "下载: https://www.python.org/downloads/"
    Write-Host "安装时请勾选 'Add Python to PATH'"
    exit 1
}

# 检查 Node.js
Write-Host "正在检查 Node.js..."
try {
    $nodeVersion = node --version 2>&1
    Write-Host "OK  Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "未找到 Node.js，请先安装 Node.js 20 LTS" -ForegroundColor Red
    Write-Host "下载: https://nodejs.org/"
    exit 1
}

# 检查 npm
Write-Host "正在检查 npm..."
try {
    $npmVersion = npm --version 2>&1
    Write-Host "OK  npm $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "未找到 npm，安装 Node.js 时会自动安装 npm" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  第 1 步：创建 Python 虚拟环境" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

Set-Location $RootDir
python -m venv .venv
Write-Host "OK  虚拟环境已创建" -ForegroundColor Green

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  第 2 步：安装后端 Python 依赖" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 激活虚拟环境并安装依赖
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

& $VenvPython -m pip install --upgrade pip
& $VenvPip install -r (Join-Path $BackendDir "requirements.txt")
Write-Host "OK  Python 依赖安装完成" -ForegroundColor Green

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  第 3 步：创建配置文件" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$EnvFile = Join-Path $BackendDir ".env"
$EnvExample = Join-Path $BackendDir ".env.example"
if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "OK  已复制 .env.example -> .env" -ForegroundColor Green
} else {
    Write-Host "OK  .env 已存在，跳过" -ForegroundColor Green
}

$DataDir = Join-Path $BackendDir "data"
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  第 4 步：安装前端依赖并构建" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

Set-Location $FrontendDir
npm install
npm run build
Write-Host "OK  前端构建完成" -ForegroundColor Green

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "启动服务：" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1"
Write-Host ""
Write-Host "访问地址：" -ForegroundColor Yellow
Write-Host "  前端: http://localhost:5173"
Write-Host "  后端: http://localhost:8000"
Write-Host "  文档: http://localhost:8000/docs"
Write-Host ""
