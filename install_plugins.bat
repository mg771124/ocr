@echo off
chcp 65001 >nul
set SRC_DIR=C:\Users\user\Desktop\ocr\mobile_plugin

echo Installing LocalOCR.lua and ScanApi.lua...

xcopy /Y "%SRC_DIR%\LocalOCR.lua" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj plugin dir (need admin)
) else (
    echo [OK] nsaj plugin dir
)

xcopy /Y "%SRC_DIR%\ScanApi.lua" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj plugin dir (need admin)
) else (
    echo [OK] nsaj plugin dir
)

xcopy /Y "%SRC_DIR%\LocalOCR.lua" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj plugin dir
) else (
    echo [OK] aaj plugin dir
)

xcopy /Y "%SRC_DIR%\ScanApi.lua" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj plugin dir
) else (
    echo [OK] aaj plugin dir
)

echo.
echo Done. Please restart Anjian mobile assistant.
pause
