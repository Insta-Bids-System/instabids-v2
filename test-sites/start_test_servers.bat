@echo off
echo Starting Instabids Test Contractor Websites...
echo.

REM Start each test site in a new terminal window
echo Starting Simple Contractor site on http://localhost:8001
start "Simple Contractor" cmd /k "cd simple-contractor && python -m http.server 8001"

echo Starting Pro Contractor site on http://localhost:8002
start "Pro Contractor" cmd /k "cd pro-contractor && python -m http.server 8002"

echo Starting Enterprise Contractor site on http://localhost:8003
start "Enterprise Contractor" cmd /k "cd enterprise-contractor && python -m http.server 8003"

echo Starting Modern Contractor site on http://localhost:8004
start "Modern Contractor" cmd /k "cd modern-contractor && python -m http.server 8004"

echo.
echo All test sites are starting up!
echo.
echo Test Sites:
echo - Simple Contact Form: http://localhost:8001
echo - Multi-Step Wizard: http://localhost:8002
echo - Enterprise Form with Validation: http://localhost:8003
echo - Modern AJAX Form: http://localhost:8004
echo.
echo To stop servers, close the terminal windows.
pause