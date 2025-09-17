@echo off
echo Starting backend server...
cd ai-agents
start /B python main.py
echo Waiting for server to start...
timeout /t 5 /nobreak > nul
cd ..
echo Running JM Holiday Lighting test...
python test_jm_simple.py
echo Test complete!
pause