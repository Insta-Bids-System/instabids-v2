@echo off
echo ========================================
echo   GitHub Authentication Setup Helper
echo ========================================
echo.
echo This script will help you set up GitHub authentication
echo.

echo Step 1: First, you need to create a Personal Access Token
echo.
echo Please open this URL in your browser:
echo https://github.com/settings/tokens
echo.
echo Instructions:
echo 1. Click "Generate new token (classic)"
echo 2. Give it a name: "Instabids Push Token"
echo 3. Select scope: "repo" (check all boxes under repo)
echo 4. Click "Generate token"
echo 5. COPY THE TOKEN - you won't see it again!
echo.
pause

echo.
echo Step 2: Enter your GitHub username and token
echo.
set /p GITHUB_USERNAME=Enter your GitHub username: 
set /p GITHUB_TOKEN=Enter your Personal Access Token: 

echo.
echo Setting up authentication...
cd /d "C:\Users\Not John Or Justin\Documents\instabids"
git remote set-url origin https://%GITHUB_USERNAME%:%GITHUB_TOKEN%@github.com/Insta-Bids-System/instabids.git

echo.
echo Step 3: Pushing to GitHub...
git push -u origin main

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   SUCCESS! Code pushed to GitHub!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Visit: https://github.com/Insta-Bids-System/instabids
    echo 2. Add secrets in Settings - Secrets and variables - Actions
    echo 3. Review GITHUB_SECRETS_SETUP.md for the secret values
) ELSE (
    echo.
    echo ========================================
    echo   Push failed. Please check:
    echo ========================================
    echo 1. Your username is correct
    echo 2. Your token has 'repo' permissions
    echo 3. You have access to the repository
)

echo.
pause
