from dataclasses import dataclass, field
from typing import Dict, List
import os

@dataclass
class SystemConfig:
    """Core system configuration with LLM settings"""
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    DEFAULT_MODEL: str = "gpt-4o"
    DOCKER_IMAGE: str = "python:3.9-slim"
    CODE_TIMEOUT: int = 60
    WORKING_DIR: str = "workspace"
    
    def __post_init__(self):
        # Configure LLM settings for autogen
        self.llm_config = {
            "config_list": [{
                "model": self.DEFAULT_MODEL,
                "api_key": self.OPENAI_API_KEY,
            }],
            "temperature": 0.7,
            "timeout": 600,
            "cache_seed": None  # Disable caching for now
        }