@echo off
chcp 65001 >nul
set SRC_DIR=C:\Users\user\Desktop\ocr\mobile_plugin

echo Installing LocalOCR / ScanApi plugin files (lua + info + html)...

set "DEST1=C:\Program Files (x86)\nsaj\nsaj\Plugin"
set "DEST2=C:\ProgramData\aaj\aaj\Plugin"

for %%F in (LocalOCR ScanApi) do (
    xcopy /Y "%SRC_DIR%\%%F.lua" "%DEST1%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] nsaj %%F.lua (need admin)
    ) else (
        echo [OK] nsaj %%F.lua
    )

    xcopy /Y "%SRC_DIR%\%%F.info" "%DEST1%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] nsaj %%F.info (need admin)
    ) else (
        echo [OK] nsaj %%F.info
    )

    xcopy /Y "%SRC_DIR%\%%F.html" "%DEST1%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] nsaj %%F.html (need admin)
    ) else (
        echo [OK] nsaj %%F.html
    )

    xcopy /Y "%SRC_DIR%\%%F.lua" "%DEST2%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] aaj %%F.lua
    ) else (
        echo [OK] aaj %%F.lua
    )

    xcopy /Y "%SRC_DIR%\%%F.info" "%DEST2%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] aaj %%F.info
    ) else (
        echo [OK] aaj %%F.info
    )

    xcopy /Y "%SRC_DIR%\%%F.html" "%DEST2%" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] aaj %%F.html
    ) else (
        echo [OK] aaj %%F.html
    )
)

echo.
echo Done. Please restart Anjian mobile assistant.
pause
