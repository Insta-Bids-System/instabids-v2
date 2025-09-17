@echo off
echo Restarting InstaBids server with Iris AI...
echo.

REM Kill any Python processes on port 8003
echo Stopping existing server on port 8003...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8003" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo Killed process %%a
)

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Change to the correct directory
cd /d "C:\Users\Not John Or Justin\Documents\instabids\ai-agents"

REM Start the server
echo.
echo Starting server with Iris AI support...
echo.
python main.py