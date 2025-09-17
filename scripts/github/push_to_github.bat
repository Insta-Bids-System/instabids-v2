@echo off
echo ========================================
echo   Instabids GitHub Push Helper
echo ========================================
echo.

:: Navigate to instabids directory
cd /d "C:\Users\Not John Or Justin\Documents\instabids"

:: Check if we're in the right directory
if not exist ".git" (
    echo ERROR: Not in a git repository!
    echo Please ensure you're in the instabids directory.
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

:: Show current status
echo Checking git status...
git status --short | find /c /v "" > temp_count.txt
set /p FILE_COUNT=<temp_count.txt
del temp_count.txt
echo Files in status: %FILE_COUNT%
echo.

:: Menu
echo What would you like to do?
echo 1. Quick push (add all, commit, push)
echo 2. Step-by-step push (recommended)
echo 3. Check status only
echo 4. Reset staged files
echo 5. Exit
echo.
set /p CHOICE=Enter your choice (1-5): 

if "%CHOICE%"=="1" goto QUICK_PUSH
if "%CHOICE%"=="2" goto STEP_BY_STEP
if "%CHOICE%"=="3" goto CHECK_STATUS
if "%CHOICE%"=="4" goto RESET
if "%CHOICE%"=="5" goto END

:QUICK_PUSH
echo.
echo === QUICK PUSH MODE ===
echo.

:: Reset first
git reset HEAD

:: Add all directories
echo Adding all files (excluding 'nul' files automatically)...
git add .gitignore README.md LICENSE package.json package-lock.json *.md *.sql *.py *.json *.bat *.sh
git add web/
git add ai-agents/
git add additional_projects/
git add agent_specifications/
git add assets/
git add database/
git add demos/
git add docs/
git add frontend/
git add knowledge/
git add mobile/
git add scripts/
git add shared/
git add supabase/
git add test-images/
git add test-sites/
git add .github/
git add .husky/

echo.
echo Files staged. Committing...
git commit -m "Complete Instabids platform with 8 AI agents, web/mobile frontends, and 5 expansion projects"

echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo === DONE! ===
pause
goto END

:STEP_BY_STEP
echo.
echo === STEP-BY-STEP MODE ===
echo.

:: Run the Python script
python github_push_helper.py

pause
goto END

:CHECK_STATUS
echo.
echo === CURRENT STATUS ===
git status
echo.
echo === STAGED FILES COUNT ===
git status --porcelain | find /c "A"
echo.
pause
goto END

:RESET
echo.
echo Resetting all staged files...
git reset HEAD
echo Done!
echo.
pause
goto END

:END
echo.
echo Thank you for using Instabids GitHub Push Helper!
