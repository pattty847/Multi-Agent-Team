@echo off
REM Setup script for Windows

REM Create necessary directories
mkdir workspace 2>nul
mkdir data 2>nul

REM Copy configuration files if they don't exist
if not exist .env (
    copy .env.template .env
    echo Created .env file from template. Please edit with your API keys.
)

REM Build and start Docker containers
docker-compose up --build -d

echo Setup complete! Please edit .env with your API keys if you haven't already.
echo To start Jupyter Lab, run: scripts\jupyter.bat