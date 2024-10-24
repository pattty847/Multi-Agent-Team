# src/agents/__init__.py
from .base import BaseAssistantAgent
from .specialized import (
    ResearchAgent,
    CodeExpertAgent,
    DataVisualizationAgent,
    ProjectManagerAgent,
    QAAgent,
    TeamManager
)
from .user_proxy import EnhancedUserProxy
from .web_agent import WebResearchAgent

__all__ = [
    'BaseAssistantAgent',
    'ResearchAgent',
    'CodeExpertAgent',
    'DataVisualizationAgent',
    'ProjectManagerAgent',
    'QAAgent',
    'TeamManager',
    'EnhancedUserProxy',
    'WebResearchAgent',
]