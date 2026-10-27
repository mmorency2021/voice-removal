@echo off
setlocal
cd /d "%~dp0"
where ffmpeg >nul 2>&1
if errorlevel 1 (
  echo FFmpeg was not found. Install it and add its bin folder to PATH.
  echo See the Windows setup section in README.md.
  goto fail
)
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>&1
  if errorlevel 1 (
    echo Install 64-bit Python 3.12 with the Python launcher first.
    goto fail
  )
  py -3.12 -m venv .venv
  if errorlevel 1 (
    py -3.11 -m venv .venv
    if errorlevel 1 goto fail
  )
)
if not exist ".venv\.audio-tools-ready" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
  echo ready>".venv\.audio-tools-ready"
)
".venv\Scripts\python.exe" -u app.py %*
if errorlevel 1 goto fail
exit /b 0
:fail
echo.
echo Setup or startup failed. Read the error above and the README troubleshooting section.
pause
exit /b 1
