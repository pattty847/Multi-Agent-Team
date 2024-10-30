# src/config/ui_config.py
from dataclasses import dataclass, field
from typing import Dict
from .base_config import BaseConfig

@dataclass
class UIConfig(BaseConfig):
    """UI-specific configuration settings"""
    # Window Configuration
    window_width: int = 1920
    window_height: int = 1080
    window_title: str = "Multi-Agent System Monitor"
    
    # Update Intervals
    metrics_update_interval: float = 1.0
    node_update_interval: float = 0.1
    
    # Display Limits
    max_messages: int = 1000
    max_history: int = 100
    
    # Theme Configuration
    theme: str = "dark"
    agent_colors: Dict[str, tuple] = field(default_factory=lambda: {
        "Research": (0, 150, 255, 255),
        "Code": (0, 255, 150, 255),
        "Viz": (255, 150, 0, 255),
        "QA": (255, 0, 150, 255),
        "PM": (150, 0, 255, 255)
    })
    
    def __post_init__(self):
        self.config_name = "ui"
        super().__post_init__()