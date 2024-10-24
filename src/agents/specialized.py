# src/agents/specialized.py
from typing import Dict, List, Optional
from autogen import AssistantAgent, ConversableAgent
from autogen import GroupChat, GroupChatManager


from src.agents.base import BaseAssistantAgent
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
        
    def _initialize_agents(self) -> Dict[str, BaseAssistantAgent]:
        """Initialize all specialized agents"""
        return {
            "research": ResearchAgent(self.config),
            "code": CodeExpertAgent(self.config),
            "viz": DataVisualizationAgent(self.config),
            "pm": ProjectManagerAgent(self.config),
            "qa": QAAgent(self.config)
        }
    
    def get_agent(self, role: str) -> Optional[BaseAssistantAgent]:
        """Get an agent by their role"""
        return self.agents.get(role)
    
    def get_all_agents(self) -> List[BaseAssistantAgent]:
        """Get all agents"""
        return list(self.agents.values())

    def execute_group_task(
        self, 
        task_description: str, 
        agents: List[BaseAssistantAgent],
        max_rounds: int = 10
    ) -> Dict:
        """
        Execute a task using a group of agents.
        
        Args:
            task_description: Description of the task to be executed
            agents: List of agents to participate in the task
            max_rounds: Maximum number of conversation rounds
            
        Returns:
            Dict containing execution results and conversation history
        """
        # Ensure we have at least one agent
        if not agents:
            raise ValueError("At least one agent is required for group task execution")
            
        # Add project manager if not present
        if self.agents["pm"] not in agents:
            agents = [self.agents["pm"]] + list(agents)
            
        # Create group chat
        groupchat = GroupChat(
            agents=agents,
            messages=[],
            max_round=max_rounds,
            speaker_selection_method="auto",
        )
        
        # Create chat manager
        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": self.config.llm_config_list},
            system_message=f"""Coordinate the completion of this task:
            {task_description}
            
            Ensure each agent contributes according to their expertise.
            The project manager should coordinate the overall effort.
            Verify results before marking the task as complete."""
        )
        
        try:
            # Start the group chat
            chat_result = agents[0].initiate_chat(
                manager,
                message=f"""Task Description:
                {task_description}
                
                Please work together to complete this task. Each agent should contribute
                based on their expertise. Begin by analyzing the requirements and creating
                a plan of action.""",
            )
            
            # Process results
            result = {
                "success": True,
                "chat_history": groupchat.messages,
                "summary": chat_result.summary if hasattr(chat_result, 'summary') else None,
                "cost": chat_result.cost if hasattr(chat_result, 'cost') else None,
                "participants": [agent.name for agent in agents]
            }
            
        except Exception as e:
            result = {
                "success": False,
                "error": str(e),
                "chat_history": groupchat.messages if 'groupchat' in locals() else [],
                "participants": [agent.name for agent in agents]
            }
            
        return result

    def execute_sequential_tasks(
        self, 
        tasks: List[Dict],
        required_agents: List[str]
    ) -> List[Dict]:
        """
        Execute a sequence of related tasks.
        
        Args:
            tasks: List of task descriptions and requirements
            required_agents: List of agent roles required for the tasks
            
        Returns:
            List of execution results for each task
        """
        results = []
        
        # Get required agents
        agents = [
            self.get_agent(role)
            for role in required_agents
            if self.get_agent(role) is not None
        ]
        
        # Execute each task in sequence
        for task in tasks:
            result = self.execute_group_task(
                task_description=task["description"],
                agents=agents,
                max_rounds=task.get("max_rounds", 10)
            )
            results.append(result)
            
            # Break if a task fails
            if not result["success"]:
                break
                
        return results