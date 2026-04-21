@echo off
echo ========================================
echo Yamato Tracker Setup & Run Script
echo ========================================

REM 1. Clone the repository
echo [Step 1/4] Cloning repository...
if exist yamato-tracker-withmap (
    echo Repository already exists. Skipping clone.
    cd yamato-tracker-withmap
) else (
    git clone https://github.com/matzoka/yamato-tracker-withmap.git
    cd yamato-tracker-withmap
)

REM 2. Create virtual environment
echo [Step 2/4] Creating virtual environment...
if not exist venv (
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM 3. Activate virtual environment and install dependencies
echo [Step 3/4] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM 4. Run the application
echo [Step 4/4] Starting Yamato Tracker...
echo ========================================
echo Setup Complete! Application is starting...
echo ========================================
streamlit run main.py

pause
