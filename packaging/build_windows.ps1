# VMPOS'ni Windows uchun yig'adi: PyInstaller (onedir) -> dist\VMPOS\VMPOS.exe
# Ishga tushirish (loyiha ildizidan):  powershell -File packaging\build_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Mahsulot rasmlari (assets\products) paketga KIRMAYDI — bu foydalanuvchi
# ma'lumoti va %LOCALAPPDATA%\VMPOS ichida saqlanadi.
python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name VMPOS `
    --icon assets\logo.ico `
    --add-data "assets\styles;assets\styles" `
    --add-data "assets\icons;assets\icons" `
    --add-data "assets\logo.png;assets" `
    --add-data "assets\logo_mark.png;assets" `
    --add-data "assets\logo.ico;assets" `
    main.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller xato bilan tugadi ($LASTEXITCODE)" }
if (-not (Test-Path "dist\VMPOS\VMPOS.exe")) { throw "dist\VMPOS\VMPOS.exe yaratilmadi" }
Write-Host "OK: dist\VMPOS\VMPOS.exe"
