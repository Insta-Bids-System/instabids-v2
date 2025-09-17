#!/bin/bash
# Quick Setup Script for Shared Instabids Development

echo "🚀 Setting up Instabids Shared Development Environment..."

# Step 1: Fix immediate port mismatch
echo "Fixing port configuration..."
sed -i 's/http:\/\/localhost:8003/http:\/\/localhost:8007/g' web/.env

# Step 2: Install dependencies
echo "Installing dependencies..."
cd web && npm install && cd ..
cd backend && pip install -r requirements.txt && cd ..

# Step 3: Start all services
echo "Starting services..."

# Create a simple process manager script
cat > start-all.bat << 'EOF'
@echo off
echo Starting Instabids Development Environment...

start "Backend" cmd /k "cd backend && python -m uvicorn main:app --reload --port 8007"
start "Frontend" cmd /k "cd web && npm run dev"
start "Supabase" cmd /k "supabase start"

echo.
echo ✅ All services started!
echo.
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8007
echo Supabase: http://localhost:54321
echo.
echo Press any key to stop all services...
pause >nul

taskkill /F /FI "WindowTitle eq Backend*" /T
taskkill /F /FI "WindowTitle eq Frontend*" /T
taskkill /F /FI "WindowTitle eq Supabase*" /T
EOF

echo "✅ Setup complete!"
echo ""
echo "To start development environment, run:"
echo "  ./start-all.bat"
echo ""
echo "For cloud deployment (recommended for multiple agents):"
echo "  1. Deploy backend to Railway: cd backend && railway up"
echo "  2. Deploy frontend to Vercel: cd web && vercel --prod"
echo "  3. Share the URLs with all agents"
