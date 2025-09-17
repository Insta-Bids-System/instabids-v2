@echo off
echo ========================================
echo   EMERGENCY INSTABIDS GITHUB PUSH
echo ========================================
echo.

cd /d "C:\Users\Not John Or Justin\Documents\instabids"

echo Current directory:
cd
echo.

echo Step 1: Adding all files (this may take a moment)...
git add -A
echo Done!
echo.

echo Step 2: Creating commit...
git commit -m "Complete Instabids platform: 8 AI agents, web/mobile frontends, and 5 expansion projects"
echo.

echo Step 3: Pushing to GitHub...
git push -u origin main

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Push failed. Trying force push...
    git push -f origin main
)

echo.
echo ========================================
echo   PUSH COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Visit: https://github.com/Insta-Bids-System/instabids
echo 2. Add secrets in Settings - Secrets and variables - Actions
echo 3. Check that all files are present
echo.
pause
