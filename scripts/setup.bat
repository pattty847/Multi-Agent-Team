# scripts/setup.bat
@echo off
SETLOCAL

:: Check if Docker Desktop is running
docker info > nul 2>&1
IF ERRORLEVEL 1 (
    echo Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    exit /b 1
)

:: Create necessary directories
mkdir ..\data 2> nul
mkdir ..\notebooks 2> nul
mkdir ..\logs 2> nul

:: Create .env file if it doesn't exist
IF NOT EXIST ..\.env (
    echo Creating .env file...
    echo OPENAI_API_KEY=your_key_here> ..\.env
    echo Please edit .env file with your OpenAI API key
)

:: Build and start containers
docker-compose -f ..\docker\docker-compose.yml build
docker-compose -f ..\docker\docker-compose.yml up -d

echo Setup complete! Jupyter Lab should be available at http://localhost:8888
echo Use 'scripts\stop.bat' to stop the containers
ENDLOCAL