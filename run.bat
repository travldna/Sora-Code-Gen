@echo off
title Sora Invite Script Runner

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Sora Invite Code script...
python sora.py

echo.
echo Script has finished. Press any key to exit...
pause >nul