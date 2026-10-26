# 安装「Claude 工牌大肥鱼」到 dsh-pet 宠物目录。
param(
    [string]$PetRoot = (Join-Path $env:USERPROFILE '.dsh\dsh-pet\pet')
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $PetRoot 'claude-dafeiyu-animation'

if (-not (Test-Path $PetRoot)) {
    throw "宠物目录不存在：$PetRoot（先装好 dsh-pet 并启动过一次）"
}

New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item (Join-Path $here 'claude-dafeiyu-config.json') (Join-Path $PetRoot 'claude-dafeiyu-config.json') -Force
Copy-Item (Join-Path $here 'animation\*.webm') $target -Force

Write-Host "已安装到：$PetRoot" -ForegroundColor Green
Write-Host "接下来：刷新 DSH 页面，或桌宠右键 →「重载配置」。" -ForegroundColor Cyan
