@echo off
REM Quick Setup Script for Shared Instabids Development

echo 🚀 Setting up Instabids Shared Development Environment...

REM Step 1: Fix port configuration
echo Fixing port configuration...
cd web
powershell -Command "(gc .env) -replace 'http://localhost:8003', 'http://localhost:8007' | Out-File -encoding ASCII .env"
cd ..

REM Step 2: Create unified start script
echo Creating unified start script...

(
echo @echo off
echo echo Starting Instabids Development Environment...
echo.
echo start "Instabids Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --port 8007"
echo timeout /t 3 /nobreak ^>nul
echo start "Instabids Frontend" cmd /k "cd web && npm run dev"
echo timeout /t 3 /nobreak ^>nul
echo start "Instabids Supabase" cmd /k "supabase start"
echo.
echo echo.
echo echo ✅ All services started!
echo echo.
echo echo Frontend: http://localhost:5173
echo echo Backend: http://localhost:8007  
echo echo Supabase: http://localhost:54321
echo echo.
echo echo To share with other agents, run: ngrok start --all
echo echo.
echo echo Press any key to stop all services...
echo pause ^>nul
echo.
echo taskkill /F /FI "WindowTitle eq Instabids*" /T 2^>nul
) > start-dev.bat

echo ✅ Setup complete!
echo.
echo To start development environment, run:
echo   start-dev.bat
echo.
echo For multiple agents working together:
echo   Option 1: Use ngrok to share local environment
echo   Option 2: Deploy to cloud (Vercel + Railway)
echo.
pause
