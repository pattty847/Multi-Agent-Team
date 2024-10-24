# src/agents/base.py
from typing import Optional, Dict
from autogen import AssistantAgent, ConversableAgent
from ..config import SystemConfig

class BaseAssistantAgent(AssistantAgent):
    """Base class for all assistant agents with common functionality"""
    def __init__(
        self,
        name: str,
        system_message: str,
        config: SystemConfig
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config={"config_list": config.llm_config_list}
        )
        self.config = config

    def save_response(self, response: str, filename: str):
        """Save agent response to file"""
        with open(filename, 'a') as f:
            f.write(f"\n{self.name}: {response}\n")