@echo off
setlocal
chcp 65001 >nul
title AI Orchestra - Multi-Agent Console

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py %*
    goto finish
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python main.py %*
    goto finish
)

echo [ERROR] Python was not found on your system.
echo Please install Python 3.10 or higher and add it to PATH.
echo Download: https://www.python.org/downloads/
pause

:finish
endlocal
