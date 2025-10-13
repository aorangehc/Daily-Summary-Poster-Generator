param(
  [string]$Name = "DailySummaryPoster",
  [switch]$OneFile = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  Write-Host "pyinstaller not installed, please run: python -m pip install pyinstaller" -ForegroundColor Yellow
  exit 1
}

$addData = "app/assets;app/assets"
if ($OneFile.IsPresent) {
  $onefileArg = "--onefile"
} else {
  $onefileArg = ""
}

pyinstaller `
  --noconfirm --windowed $onefileArg `
  --name $Name `
  --add-data $addData `
  app/main.py

Write-Host "Build completed, output in dist/ directory." -ForegroundColor Green

