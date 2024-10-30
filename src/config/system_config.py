# src/config/system_config.py
from dataclasses import dataclass, field
import os
from .base_config import BaseConfig
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemConfig(BaseConfig):
    """System-wide configuration settings"""
    # OpenAI API Configuration
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    default_model: str = "gpt-4"
    request_timeout: int = 60
    max_tokens: int = 2000
    
    # Docker Configuration
    docker_image: str = "python:3.9-slim"
    container_memory_limit: str = "512m"
    container_cpu_limit: float = 0.5
    workspace_dir: str = "workspace"
    
    # Agent Configuration
    max_agents: int = 10
    agent_timeout: int = 300
    max_retries: int = 3
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "system.log"
    max_log_size: int = 10_000_000  # 10MB
    backup_count: int = 5
    
    # Version info
    version: str = "1.0.0"

    def __post_init__(self):
        self.config_name = "system"
        super().__post_init__()  # This will call BaseConfig's _load_config
        self._validate_config()
        
    def _validate_config(self):
        """Validate configuration settings"""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not set")
        
        if self.max_tokens > 4096:
            logger.warning("max_tokens exceeds model limit, setting to 4096")
            self.max_tokens = 4096