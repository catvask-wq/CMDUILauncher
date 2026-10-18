@echo off
:: === 1. Check for administrator rights (UAC elevation) ===
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: Return to the script folder (UAC changes the working directory)
cd /d "%~dp0"

:: === 2. Check if Python is available ===
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Python not found in PATH.
    echo Install Python from python.org and check "Add to PATH".
    pause
    exit /b
)

:: === 3. Virtual environment ===
if not exist "venv" (
    echo Creating isolated environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

:: === 4. Install dependencies if needed ===
python -c "import PyQt6" >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing PyQt6...
    pip install PyQt6
)

:: === 5. Start the GUI ===
echo Starting graphical shell...
python cmdui.py

:: === 6. Pause so error messages stay visible ===
pause
