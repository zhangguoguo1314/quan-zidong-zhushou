# 全自动助手 - Windows 启动脚本
# 使用方法: powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$VenvDir = Join-Path $RootDir ".venv"
$VenvUvicorn = Join-Path $VenvDir "Scripts\uvicorn.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "未找到 .venv，请先运行 scripts\install-windows.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  全自动助手 - 启动服务" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# 启动后端
Write-Host "启动后端 FastAPI (端口 8000)" -ForegroundColor Green
$BackendJob = Start-Job -ScriptBlock {
    param($Uvicorn, $BackendDir)
    Set-Location $BackendDir
    & $Uvicorn main:app --host 127.0.0.1 --port 8000
} -ArgumentList $VenvUvicorn, $BackendDir

Write-Host "  后端作业ID: $($BackendJob.Id)" -ForegroundColor Gray

# 启动前端
Write-Host "启动前端 Vite (端口 5173)" -ForegroundColor Green
Write-Host ""
Write-Host "  访问地址："
Write-Host "    前端: http://localhost:5173"
Write-Host "    后端: http://localhost:8000"
Write-Host "    文档: http://localhost:8000/docs"
Write-Host ""
Write-Host "  按 Ctrl+C 停止所有服务"
Write-Host ""

Set-Location $FrontendDir

try {
    npm run dev
} finally {
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -Force -ErrorAction SilentlyContinue
    Write-Host "服务已停止" -ForegroundColor Green
}
