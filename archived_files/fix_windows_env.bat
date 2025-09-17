@echo off
echo Removing conflicting Supabase environment variables...

:: Remove system environment variables
setx SUPABASE_URL ""
setx SUPABASE_SERVICE_ROLE ""
setx SUPABASE_ANON_KEY ""

:: Also remove from current session
set SUPABASE_URL=
set SUPABASE_SERVICE_ROLE=
set SUPABASE_ANON_KEY=

echo.
echo Environment variables cleared!
echo Please close and reopen your terminal for changes to take effect.
echo.
pause