from dataclasses import dataclass
from pathlib import Path
import yaml
import os
from typing import Dict, Any

@dataclass 
class SystemConfig:
    """Core system settings"""
    log_level: str = "INFO"
    log_file: str = "system.log"
    max_log_size: int = 10_000_000
    backup_count: int = 5
    openai_api_key: str = ""
    max_agents: int = 10
    # Docker Configuration
    docker_image: str = "python:3.9-slim"
    container_memory_limit: str = "512m"
    container_cpu_limit: float = "0.5"
    workspace_dir: str = "workspace"

@dataclass
class UIConfig:
    """UI settings"""
    window_title: str = "Multi-Agent System Monitor"
    window_width: int = 1920
    window_height: int = 1080
    window_resulution_pct: float = 0.8
    theme: str = "dark"

class ConfigManager:
    """Simple config manager with dataclass defaults and YAML overrides"""
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        
        # Load core configs with dataclass defaults
        self.system = SystemConfig()
        self.ui = UIConfig()
        
        # Override with YAML if exists
        self._load_yaml_overrides()
        
        # Load agent configs from YAML (these can stay flexible)
        self.agent_configs = self._load_agent_configs()
        
        # Handle environment variables
        self.system.openai_api_key = os.getenv('OPENAI_API_KEY', self.system.openai_api_key)

    def _load_yaml_overrides(self):
        """Load YAML overrides for core configs"""
        if (self.config_dir / "system.yaml").exists():
            with open(self.config_dir / "system.yaml") as f:
                system_yaml = yaml.safe_load(f)
                for k, v in system_yaml.items():
                    if hasattr(self.system, k):
                        setattr(self.system, k, v)
                        
        if (self.config_dir / "ui.yaml").exists():
            with open(self.config_dir / "ui.yaml") as f:
                ui_yaml = yaml.safe_load(f)
                for k, v in ui_yaml.items():
                    if hasattr(self.ui, k):
                        setattr(self.ui, k, v)

    def _load_agent_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load agent configs from YAML"""
        agent_configs = {}
        for config_file in self.config_dir.glob("agent_*.yaml"):
            with open(config_file) as f:
                config = yaml.safe_load(f)
                if config and 'name' in config:
                    agent_configs[config['name']] = config
        return agent_configs

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get agent configuration"""
        return self.agent_configs.get(agent_name, {})