# src/config/agent_config.py
from dataclasses import dataclass, field
from typing import List
from .base_config import BaseConfig
import logging

logger = logging.getLogger(__name__)

from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentConfig:
    """Agent-specific configuration settings"""
    # Non-default fields
    name: str
    agent_type: str
    
    # Default fields
    system_message: str = ""
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    memory_limit: str = "256m"
    cpu_limit: float = 0.25
    timeout: int = 60
    allowed_actions: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.config_name = f"agent_{self.name}"
        self._load_config()
        self._validate_agent_config()
        
    def _validate_agent_config(self):
        """Validate agent-specific configuration"""
        if not self.name or not self.agent_type:
            raise ValueError("Agent name and type are required")
            
        if self.temperature < 0 or self.temperature > 1:
            logger.warning("Temperature should be between 0 and 1")
            self.temperature = max(0, min(1, self.temperature))