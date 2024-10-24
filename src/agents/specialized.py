# src/agents/specialized.py
from typing import Dict, List, Optional
from autogen import AssistantAgent, ConversableAgent
from ..config import SystemConfig

class ResearchAgent(AssistantAgent):
    """Specializes in academic research and paper analysis"""
    def __init__(self, config: SystemConfig):
        super().__init__(
            name="research_assistant",
            system_message="""You are a research specialist focused on analyzing academic papers and research findings.
            Your strengths include:
            1. Summarizing complex research papers
            2. Identifying key findings and methodologies
            3. Comparing different research approaches
            4. Suggesting relevant papers and citations
            
            Always structure your responses clearly and cite sources when available.
            Include links to papers when possible.""",
            llm_config={"config_list": config.llm_config_list}
        )

class CodeExpertAgent(AssistantAgent):
    """Specializes in code analysis, optimization, and best practices"""
    def __init__(self, config: SystemConfig):
        super().__init__(
            name="code_expert",
            system_message="""You are a code expert specialized in:
            1. Code review and optimization
            2. Best practices and design patterns
            3. Performance analysis
            4. Security review
            
            When analyzing code:
            1. First identify potential issues
            2. Suggest specific improvements
            3. Provide example code when helpful
            4. Consider both functionality and maintainability""",
            llm_config={"config_list": config.llm_config_list}
        )

class DataVisualizationAgent(AssistantAgent):
    """Specializes in creating and explaining data visualizations"""
    def __init__(self, config: SystemConfig):
        super().__init__(
            name="visualization_expert",
            system_message="""You are a data visualization specialist who excels at:
            1. Creating clear and informative visualizations
            2. Choosing appropriate chart types
            3. Color theory and accessibility
            4. Interactive visualization design
            
            Always consider:
            1. The target audience
            2. The story the data tells
            3. Best practices in visualization
            4. Performance and interactivity""",
            llm_config={"config_list": config.llm_config_list}
        )

class ProjectManagerAgent(AssistantAgent):
    """Coordinates tasks and manages workflow between agents"""
    def __init__(self, config: SystemConfig):
        super().__init__(
            name="project_manager",
            system_message="""You are a project manager responsible for:
            1. Task coordination between different agents
            2. Workflow optimization
            3. Progress tracking
            4. Resource allocation
            
            Your role is to:
            1. Break down complex tasks
            2. Assign work to appropriate specialists
            3. Monitor progress and handle blockers
            4. Ensure quality and completeness""",
            llm_config={"config_list": config.llm_config_list}
        )

class QAAgent(AssistantAgent):
    """Specializes in testing and quality assurance"""
    def __init__(self, config: SystemConfig):
        super().__init__(
            name="qa_expert",
            system_message="""You are a QA specialist focused on:
            1. Test case design
            2. Edge case identification
            3. Performance testing
            4. User experience testing
            
            Always:
            1. Think about potential failure modes
            2. Consider different user scenarios
            3. Verify requirements are met
            4. Document test results clearly""",
            llm_config={"config_list": config.llm_config_list}
        )

class TeamManager:
    """Manages a team of specialized agents"""
    def __init__(self, config: SystemConfig, executor):
        self.config = config
        self.executor = executor
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, AssistantAgent]:
        """Initialize all specialized agents"""
        return {
            "research": ResearchAgent(self.config),
            "code": CodeExpertAgent(self.config),
            "viz": DataVisualizationAgent(self.config),
            "pm": ProjectManagerAgent(self.config),
            "qa": QAAgent(self.config)
        }
    
    def get_agent(self, role: str) -> Optional[AssistantAgent]:
        """Get an agent by their role"""
        return self.agents.get(role)
    
    def get_all_agents(self) -> List[AssistantAgent]:
        """Get all agents"""
        return list(self.agents.values())