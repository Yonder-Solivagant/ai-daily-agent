@echo off
rem ===== Job2: task entry launched by Windows Task Scheduler =====
rem NOTE: keep this file pure ASCII (cmd.exe reads .cmd in the system ANSI codepage).
cd /d "%~dp0"
set PYTHONUNBUFFERED=1
if not exist "logs" mkdir logs
set LOG=%~dp0logs\task_console.log
echo. >> "%LOG%"
echo ==== task launched %date% %time% ==== >> "%LOG%"
".venv\Scripts\python.exe" run_once.py >> "%LOG%" 2>&1
echo ==== task finished, exit code %ERRORLEVEL% %date% %time% ==== >> "%LOG%"
exit /b %ERRORLEVEL%
