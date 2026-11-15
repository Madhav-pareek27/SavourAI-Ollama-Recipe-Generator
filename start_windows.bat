@echo off
setlocal
cd /d "%~dp0"
echo.
echo  ==========================================
echo    SavourAI - 100%% LOCAL AI WITH OLLAMA
 echo  ==========================================
echo.
where ollama >nul 2>nul
if errorlevel 1 (
    echo WARNING: ollama was not found in PATH. Install or start Ollama first.
    echo https://ollama.com/download
    echo.
) else (
    echo Available Ollama models:
    ollama list
    echo.
)
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3.12 -m venv .venv 2>nul
    if errorlevel 1 (
        echo Python 3.12 not found, trying default Python...
        py -m venv .venv
    )
    if errorlevel 1 (
        echo Could not create virtual environment. Install Python 3.12.
        pause
        exit /b 1
    )
)
echo Installing local app dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Package installation failed. Check your internet for initial installation.
    pause
    exit /b 1
)
echo.
echo Starting SavourAI on http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py
pause
