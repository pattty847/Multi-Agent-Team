@echo off
echo Jupyter Lab is running at http://localhost:8888
docker-compose -f ..\docker\docker-compose.yml logs -f multi_agent