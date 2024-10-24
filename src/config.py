import os
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class SystemConfig:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL: str = "gpt-4o"
    DOCKER_IMAGE: str = "python:3.12-slim"
    CODE_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    WORKING_DIR: str = "workspace"

    @property
    def llm_config_list(self) -> List[Dict]:
        return [
            {
                "model": self.DEFAULT_MODEL,
                "api_key": self.OPENAI_API_KEY
            }
        ]