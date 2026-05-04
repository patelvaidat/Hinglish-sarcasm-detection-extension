@echo off
REM Startup script for Windows

echo ==========================================
echo Sarcasm Detection API - Startup
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
echo Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if model exists
if not exist "saved_model" (
    echo Warning: saved_model directory not found!
    echo Please place your trained MuRIL model in the saved_model\ directory
    echo Required files:
    echo   - config.json
    echo   - pytorch_model.bin
    echo   - tokenizer files
    exit /b 1
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
if not exist "data" mkdir data

REM Start the server
echo.
echo ==========================================
echo Starting API server on port 8000...
echo ==========================================
echo.
echo API will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
