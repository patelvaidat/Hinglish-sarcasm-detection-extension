@echo off
REM Master setup and run script for Sarcasm Detection System (Windows)

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
set VENV_PATH=%PROJECT_ROOT%venv311
set BACKEND_DIR=%PROJECT_ROOT%backend

echo.
echo ============================================================
echo     SARCASM DETECTION SYSTEM - SETUP ^& RUN (Windows)
echo ============================================================
echo.

REM Check Python version
echo Checking Python version...
python.exe --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11 or later.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python.exe --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Step 1: Create virtual environment if needed
echo.
echo Setting up virtual environment...
if not exist "%VENV_PATH%" (
    echo Creating new virtual environment at %VENV_PATH%...
    python.exe -m venv "%VENV_PATH%"
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
call "%VENV_PATH%\Scripts\activate.bat"
echo [OK] Virtual environment activated

REM Step 2: Install dependencies
echo.
echo Checking dependencies...
python.exe -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install --upgrade pip
    pip install -r "%BACKEND_DIR%\requirements.txt"
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)

REM Step 3: Check for model
echo.
echo Checking for trained model...
if not exist "%BACKEND_DIR%\saved_model" (
    echo WARNING: No model found in %BACKEND_DIR%\saved_model\
    echo.
    set /p DOWNLOAD="Download a test model? (y/n): "
    if /i "!DOWNLOAD!"=="y" (
        echo Downloading test model...
        cd /d "%BACKEND_DIR%"
        python download_test_model.py
        cd /d "%PROJECT_ROOT%"
        echo [OK] Test model downloaded
    ) else (
        echo ERROR: Model is required. Please place model files in %BACKEND_DIR%\saved_model\
        pause
        exit /b 1
    )
) else (
    echo [OK] Model found at %BACKEND_DIR%\saved_model\
)

REM Step 4: Create required directories
echo.
echo Creating required directories...
if not exist "%BACKEND_DIR%\logs" mkdir "%BACKEND_DIR%\logs"
if not exist "%BACKEND_DIR%\reports" mkdir "%BACKEND_DIR%\reports"
if not exist "%BACKEND_DIR%\data" mkdir "%BACKEND_DIR%\data"
echo [OK] Directories ready

REM Step 5: Set environment
echo.
echo Setting up environment variables...
set MODEL_PATH=%BACKEND_DIR%\saved_model
echo [OK] MODEL_PATH=%MODEL_PATH%

REM Step 6: Start backend
echo.
echo ============================================================
echo              STARTING BACKEND SERVER
echo ============================================================
echo.
echo Starting Uvicorn server...
echo   Host: 0.0.0.0
echo   Port: 8000
echo   Model: %MODEL_PATH%
echo.
echo Access the API at:
echo   - http://localhost:8000
echo   - http://localhost:8000/docs (interactive docs)
echo   - http://localhost:8000/health (health check)
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%BACKEND_DIR%"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
