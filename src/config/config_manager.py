# src/config/config_manager.py
from typing import Dict
import yaml
import logging
from pathlib import Path

from src.config.agent_config import AgentConfig
from .system_config import SystemConfig
from .ui_config import UIConfig

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages all configuration instances"""
    def __init__(self):
        self.system_config = SystemConfig()
        self.ui_config = UIConfig()
        self.agent_configs: Dict[str, AgentConfig] = {}
        
    def create_agent_config(self, name: str, agent_type: str, **kwargs) -> AgentConfig:
        """Create and store a new agent configuration"""
        config = AgentConfig(name=name, agent_type=agent_type, **kwargs)
        self.agent_configs[name] = config
        return config
        
    def load_all_configs(self):
        """Load all configurations"""
        self.system_config = SystemConfig()
        self.ui_config = UIConfig()
        
        # Load agent configs from config directory
        config_dir = Path("configs")
        for config_file in config_dir.glob("agent_*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    name = config_data.get('name')
                    agent_type = config_data.get('agent_type')
                    if name and agent_type:
                        self.create_agent_config(name, agent_type, **config_data)
            except Exception as e:
                logger.error(f"Error loading agent config {config_file}: {e}")
                
    def save_all_configs(self):
        """Save all configurations"""
        self.system_config.save_config()
        self.ui_config.save_config()
        for agent_config in self.agent_configs.values():
            agent_config.save_config()
            
    def get_agent_config(self, name: str) -> AgentConfig:
        """Get agent configuration by name"""
        return self.agent_configs.get(name)
    
    def update_agent_config(self, name: str, **kwargs):
        """Update existing agent configuration"""
        if config := self.agent_configs.get(name):
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.save_config()