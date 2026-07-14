@echo off
REM 03_auto_scrape.bat - Windows auto incremental scrape entry (Task Scheduler, every 2 hours)
REM Reads accounts.txt, scrapes new tweets from the last 7 days, sends email report if any.

cd /d "%~dp0"

REM Prevent duplicate runs (directory lock)
set "LOCKDIR=%~dp0.scrape.lock"
mkdir "%LOCKDIR%" 2>nul
if errorlevel 1 (
    echo %date% %time% Another instance is running, skipping.
    exit /b 0
)

if not exist "%~dp0logs" mkdir "%~dp0logs"
set "LOG=%~dp0logs\auto_scrape.log"

echo ==================== %date% %time% auto check started ==================== >> "%LOG%"

REM Prefer the py launcher, fall back to python on PATH
set "PY=py -3"
where py >nul 2>nul || set "PY=python"

REM Force UTF-8 so the log file is readable (Python prints Chinese)
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

%PY% -u "%~dp001_x_following_scraper.py" --incremental --translate --images --report >> "%LOG%" 2>&1
set "CODE=%errorlevel%"

echo ==================== %date% %time% finished (exit=%CODE%) ==================== >> "%LOG%"

rmdir "%LOCKDIR%"
exit /b %CODE%
