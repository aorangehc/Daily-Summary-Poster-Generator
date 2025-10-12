param(
  [string]$Name = "DailySummaryPoster",
  [switch]$OneFile = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  Write-Host "pyinstaller 未安装，请先执行: python -m pip install pyinstaller" -ForegroundColor Yellow
  exit 1
}

$addData = "app/assets;app/assets"
$onefileArg = $OneFile.IsPresent ? "--onefile" : ""

pyinstaller `
  --noconfirm --windowed $onefileArg `
  --name $Name `
  --add-data $addData `
  app/main.py

Write-Host "构建完成，产物位于 dist/ 目录。" -ForegroundColor Green

