# src/config/agent_config.py
from dataclasses import dataclass, field
from typing import List
from .base_config import BaseConfig
import logging

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig(BaseConfig):
    """Agent-specific configuration settings"""
    # Required fields
    name: str
    agent_type: str
    
    # Optional fields with defaults
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
        """Post initialization handling"""
        # First validate required fields
        self._validate_agent_config()
        
        # Set config name before loading
        self.config_name = f"agent_{self.name}"
        
        # Load configuration from file (inherited from BaseConfig)
        super().__post_init__()
        
        # Revalidate after loading to ensure loaded values are valid
        self._validate_agent_config()
        
    def _validate_agent_config(self):
        """Validate agent-specific configuration"""
        if not self.name or not self.agent_type:
            raise ValueError("Agent name and type are required")
            
        if self.temperature < 0 or self.temperature > 1:
            logger.warning("Temperature should be between 0 and 1")
            self.temperature = max(0, min(1, self.temperature))