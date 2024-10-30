# src/config/base_config.py
from dataclasses import dataclass, field
from typing import Dict, Any
import yaml
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BaseConfig:
    """Base configuration class with common functionality"""
    config_path: Path = field(default_factory=lambda: Path("configs"))
    config_name: str = field(default="base")
    
    def __post_init__(self):
        """Post initialization hook to load configuration"""
        self.config_file = self.config_path / f"{self.config_name}.yaml"
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:  # Check if file is not empty
                        for key, value in config_data.items():
                            if hasattr(self, key):
                                setattr(self, key, value)
        except Exception as e:
            logger.error(f"Error loading config {self.config_name}: {e}")
            
    def save_config(self):
        """Save current configuration to file"""
        try:
            self.config_path.mkdir(parents=True, exist_ok=True)
            config_data = self.to_dict()
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(config_data, f)
        except Exception as e:
            logger.error(f"Error saving config {self.config_name}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_') and key not in ['config_path', 'config_file']
        }