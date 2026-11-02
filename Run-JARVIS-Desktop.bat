@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Create and activate a virtual environment, then install requirements-desktop.txt first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m app.desktop
pause
