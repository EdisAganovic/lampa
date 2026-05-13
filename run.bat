@echo off
title MELK-OA10 Controller
echo Starting MELK-OA10 Bluetooth Lamp Controller...

:: Ensure dependencies are synced (optional but recommended for uv)
:: uv sync

:: Run the application using uv
uv run gui_lamp.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed or failed to start.
    echo Please make sure your Bluetooth is turned on and 'uv' is installed.
    pause
)
