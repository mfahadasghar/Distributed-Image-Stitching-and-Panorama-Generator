@echo off
REM Distributed Image Stitching and Panorama Generator
REM Startup script for Windows

echo ========================================
echo   Image Stitching ^& Panorama Generator
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install/update requirements
echo Installing dependencies...
pip install -q -r requirements.txt

REM Create necessary directories
echo Setting up directories...
if not exist "uploads\" mkdir uploads
if not exist "outputs\" mkdir outputs

REM Run the application
echo.
echo Starting server...
echo ========================================
python app.py

pause
