import os
import logging
import asyncio
import docker
from pathlib import Path
from typing import Dict, List, Optional
from docker.errors import NotFound, APIError

class DockerWorkspaceManager:
    """Manages persistent Docker workspace and package caching with enhanced functionality"""
    
    def __init__(self, base_dir: str = "docker_workspace"):
        self.base_dir = Path(base_dir)
        self.volumes_dir = self.base_dir / "volumes"
        self.packages_dir = self.base_dir / "packages"
        self.workspace_dir = self.base_dir / "workspace"
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logging.info("Docker client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Docker client: {e}")
            raise
        
        # Create necessary directories
        self._create_directories()
        
        # Create or get volume names
        self.pip_cache_volume = "pip_cache_volume"
        self.workspace_volume = "workspace_volume"
        
        # Container tracking
        self.active_containers: Dict[str, docker.models.containers.Container] = {}
        
    def _create_directories(self):
        """Create necessary directories with proper permissions"""
        try:
            for directory in [self.volumes_dir, self.packages_dir, self.workspace_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                # Ensure directory has proper permissions (read/write for user)
                os.chmod(directory, 0o755)
            logging.info("Workspace directories created successfully")
        except Exception as e:
            logging.error(f"Failed to create directories: {e}")
            raise

    def ensure_volumes(self):
        """Ensure Docker volumes exist with proper configuration"""
        try:
            volume_configs = {
                self.pip_cache_volume: {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(self.volumes_dir / "pip_cache")
                    }
                },
                self.workspace_volume: {
                    "driver": "local",
                    "driver_opts": {
                        "type": "none",
                        "o": "bind",
                        "device": str(self.workspace_dir)
                    }
                }
            }
            
            for volume_name, config in volume_configs.items():
                try:
                    self.docker_client.volumes.get(volume_name)
                    logging.info(f"Volume {volume_name} already exists")
                except NotFound:
                    self.docker_client.volumes.create(name=volume_name, **config)
                    logging.info(f"Created volume {volume_name}")
                    
        except Exception as e:
            logging.error(f"Error ensuring Docker volumes: {e}")
            raise

    def get_volume_config(self) -> Dict:
        """Get Docker volume configuration for code execution with enhanced security"""
        return {
            "use_docker": True,
            "work_dir": str(self.workspace_dir),
            "volumes": {
                self.pip_cache_volume: {
                    "bind": "/root/.cache/pip",
                    "mode": "ro"  # Read-only for security
                },
                self.workspace_volume: {
                    "bind": "/workspace",
                    "mode": "rw"
                }
            },
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "network_mode": "none"  # Disable network access for security
        }

    async def cleanup_unused(self):
        """Clean up unused containers while preserving volumes"""
        try:
            # Get list of containers with our label
            containers = self.docker_client.containers.list(
                all=True,
                filters={
                    "label": "created_by=enhanced_code_agent",
                    "status": "exited"
                }
            )
            
            # Track cleanup statistics
            cleanup_stats = {
                "removed": 0,
                "failed": 0,
                "errors": []
            }
            
            for container in containers:
                try:
                    # Get container age
                    created = container.attrs['Created']
                    container_age = await self._get_container_age(created)
                    
                    # Remove if older than 1 hour
                    if container_age > 3600:  # 1 hour in seconds
                        container.remove(force=True)
                        cleanup_stats["removed"] += 1
                        logging.info(f"Removed unused container: {container.id}")
                        
                        # Remove from tracking if present
                        self.active_containers.pop(container.id, None)
                        
                except Exception as e:
                    cleanup_stats["failed"] += 1
                    cleanup_stats["errors"].append(f"Error removing container {container.id}: {str(e)}")
                    logging.warning(f"Error removing container {container.id}: {e}")
            
            # Log cleanup summary
            logging.info(f"Cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            raise

    async def _get_container_age(self, created_time: str) -> float:
        """Calculate container age in seconds"""
        try:
            created = docker.utils.datetime_to_timestamp(created_time)
            current = docker.utils.datetime_to_timestamp(docker.utils.datetime.datetime.now())
            return current - created
        except Exception as e:
            logging.error(f"Error calculating container age: {e}")
            return 0

    def create_container(self, image: str, command: str, **kwargs) -> str:
        """Create a new container with proper resource limits and tracking"""
        try:
            container = self.docker_client.containers.create(
                image=image,
                command=command,
                labels={"created_by": "enhanced_code_agent"},
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,  # Limit to 0.5 CPU
                **kwargs
            )
            
            # Track the container
            self.active_containers[container.id] = container
            logging.info(f"Created container: {container.id}")
            
            return container.id
            
        except Exception as e:
            logging.error(f"Error creating container: {e}")
            raise

    def close(self):
        """Close Docker client and cleanup resources"""
        try:
            # Stop and remove all active containers
            for container_id, container in self.active_containers.items():
                try:
                    container.stop(timeout=10)
                    container.remove(force=True)
                    logging.info(f"Cleaned up container: {container_id}")
                except Exception as e:
                    logging.warning(f"Error cleaning up container {container_id}: {e}")
            
            # Close Docker client
            if self.docker_client:
                self.docker_client.close()
                logging.info("Docker client closed successfully")
                
            # Clear tracking
            self.active_containers.clear()
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            raise