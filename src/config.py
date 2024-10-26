from dataclasses import dataclass
import os

@dataclass
class SystemConfig:
    """Core system configuration"""
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-4o"
    DOCKER_IMAGE: str = "python:3.9-slim"
    CODE_TIMEOUT: int = 60
    WORKING_DIR: str = "workspace"