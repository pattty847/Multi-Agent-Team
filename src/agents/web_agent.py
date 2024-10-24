# src/agents/web_agent.py
from typing import Dict

from tools.web_search import WebSearchTool
from .base import BaseAssistantAgent

class WebResearchAgent(BaseAssistantAgent):
    """Agent specialized in web research with integrated search capabilities"""
    def __init__(self, config):
        super().__init__(
            name="web_researcher",
            system_message="""You are a web research specialist who can:
            1. Search for recent academic papers and research
            2. Analyze and summarize findings
            3. Compare different sources
            4. Identify key trends and developments
            
            Always cite sources and provide links when available.""",
            config=config
        )
        self.search_tool = WebSearchTool()
    
    def research(self, query: str) -> Dict:
        """Perform research on a given query"""
        return self.search_tool.summarize_research(query)