@echo off
chcp 65001 >nul
set SRC_DIR=C:\Users\user\Desktop\ocr\mobile_plugin

echo Installing LocalOCR.lua and ScanApi.lua...

xcopy /Y "%SRC_DIR%\LocalOCR.lua" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj LocalOCR.lua (need admin)
) else (
    echo [OK] nsaj LocalOCR.lua
)

xcopy /Y "%SRC_DIR%\LocalOCR.info" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj LocalOCR.info (need admin)
) else (
    echo [OK] nsaj LocalOCR.info
)

xcopy /Y "%SRC_DIR%\ScanApi.lua" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj ScanApi.lua (need admin)
) else (
    echo [OK] nsaj ScanApi.lua
)

xcopy /Y "%SRC_DIR%\ScanApi.info" "C:\Program Files (x86)\nsaj\nsaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] nsaj ScanApi.info (need admin)
) else (
    echo [OK] nsaj ScanApi.info
)

xcopy /Y "%SRC_DIR%\LocalOCR.lua" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj LocalOCR.lua
) else (
    echo [OK] aaj LocalOCR.lua
)

xcopy /Y "%SRC_DIR%\LocalOCR.info" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj LocalOCR.info
) else (
    echo [OK] aaj LocalOCR.info
)

xcopy /Y "%SRC_DIR%\ScanApi.lua" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj ScanApi.lua
) else (
    echo [OK] aaj ScanApi.lua
)

xcopy /Y "%SRC_DIR%\ScanApi.info" "C:\ProgramData\aaj\aaj\Plugin" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] aaj ScanApi.info
) else (
    echo [OK] aaj ScanApi.info
)

echo.
echo Done. Please restart Anjian mobile assistant.
pause
