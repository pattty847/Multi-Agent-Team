import os
from typing import Dict, List, Optional
import logging
import docker
from pathlib import Path

class DockerWorkspaceManager:
    """Manages persistent Docker workspace and package caching"""
    
    def __init__(self, base_dir: str = "docker_workspace"):
        self.base_dir = Path(base_dir)
        self.volumes_dir = self.base_dir / "volumes"
        self.packages_dir = self.base_dir / "packages"
        self.workspace_dir = self.base_dir / "workspace"
        self.docker_client = docker.from_env()
        
        # Create necessary directories
        self.volumes_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create or get volume names
        self.pip_cache_volume = "pip_cache_volume"
        self.workspace_volume = "workspace_volume"
        
    def ensure_volumes(self):
        """Ensure Docker volumes exist"""
        try:
            # Create pip cache volume if it doesn't exist
            try:
                self.docker_client.volumes.get(self.pip_cache_volume)
            except docker.errors.NotFound:
                self.docker_client.volumes.create(
                    name=self.pip_cache_volume,
                    driver='local'
                )
                
            # Create workspace volume if it doesn't exist
            try:
                self.docker_client.volumes.get(self.workspace_volume)
            except docker.errors.NotFound:
                self.docker_client.volumes.create(
                    name=self.workspace_volume,
                    driver='local'
                )
                
        except Exception as e:
            logging.error(f"Error ensuring Docker volumes: {e}")
            raise

    def get_volume_config(self) -> Dict:
        """Get Docker volume configuration for code execution"""
        return {
            "use_docker": True,
            "work_dir": str(self.workspace_dir),
            "volumes": {
                self.pip_cache_volume: {
                    "bind": "/root/.cache/pip",
                    "mode": "rw"
                },
                self.workspace_volume: {
                    "bind": "/workspace",
                    "mode": "rw"
                }
            }
        }

    async def cleanup_unused(self):
        """Clean up unused containers while preserving volumes"""
        try:
            containers = self.docker_client.containers.list(
                all=True,
                filters={
                    "label": "created_by=enhanced_code_agent",
                    "status": "exited"
                }
            )
            
            for container in containers:
                try:
                    container.remove()
                    logging.info(f"Removed unused container: {container.id}")
                except Exception as e:
                    logging.warning(f"Error removing container {container.id}: {e}")
                    
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

    def close(self):
        """Close Docker client"""
        if self.docker_client:
            self.docker_client.close()