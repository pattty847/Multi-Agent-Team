# src/agents/specialized.py
from typing import Dict, List, Optional
from autogen import AssistantAgent, ConversableAgent
from autogen import GroupChat, GroupChatManager
from src.agents.base import BaseAssistantAgent
from typing import Dict, List, Any, Optional, Callable
from autogen import ConversableAgent
from autogen.agentchat import UserProxyAgent
import docker
import logging
import os
from pathlib import Path

from src.core.config import SystemConfig

logger = logging.getLogger(__name__)

class SpecializedCodeAgent(ConversableAgent):
    """
    An enhanced CodeExpertAgent that specializes in code generation, review, and execution
    using Docker containers for isolation and safety.
    """
    
    DEFAULT_CONFIG = {
        "temperature": 0.1,  # Lower temperature for more focused code generation
        "model": "gpt-4o",  # Using latest model for better code understanding
        "timeout": 600,  # 10 minute timeout for complex operations
    }

    DEFAULT_SYSTEM_MESSAGE = """You are an expert software developer with deep knowledge of 
    software architecture, design patterns, and best practices. Your role is to:
    1. Write high-quality, well-documented code
    2. Review and improve existing code
    3. Suggest architectural improvements
    4. Execute and test code safely in containers
    5. Explain technical concepts clearly
    
    Always follow these principles:
    - Write secure, efficient, and maintainable code
    - Provide clear documentation and explanations
    - Use appropriate design patterns and best practices
    - Consider scalability and performance implications
    """

    def __init__(
        self,
        name: str = "CodeExpert",
        human_input_mode: str = "TERMINATE",
        system_message: Optional[str] = DEFAULT_SYSTEM_MESSAGE,
        llm_config: Optional[Dict] = None,
        code_execution_config: Optional[Dict] = None,
        **kwargs
    ):
        """Initialize the CodeExpertAgent with enhanced capabilities."""
        
        # Setup base configuration
        self.code_execution_config = {
            "work_dir": "./workspace",
            "use_docker": True,
            "timeout": 300,
            "last_n_messages": 3,
        }
        
        # Initialize Docker client if using containers
        self.docker_client = docker.from_env() if self.code_execution_config["use_docker"] else None
        
        # Setup workspace directory
        self.workspace_dir = Path(self.code_execution_config["work_dir"])
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Create UserProxyAgent for code execution
        self.executor = UserProxyAgent(
            name="CodeExecutor",
            human_input_mode="NEVER",
            code_execution_config=self.code_execution_config,
            system_message="I am a code execution agent. I run code safely and return results."
        )

        # Initialize with parent class
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            llm_config=llm_config or self.DEFAULT_CONFIG,
            code_execution_config=False,  # We handle code execution ourselves
            **kwargs
        )

        # Register message handlers
        self.register_reply(
            trigger=self._is_code_execution_request,
            reply_func=self._handle_code_execution
        )
        self.register_reply(
            trigger=self._is_code_review_request,
            reply_func=self._handle_code_review
        )

    def _is_code_execution_request(self, message: Dict) -> bool:
        """Determine if the message is requesting code execution."""
        content = message.get("content", "").lower()
        execution_keywords = {"run", "execute", "test", "try", "run this"}
        return any(keyword in content for keyword in execution_keywords)

    def _is_code_review_request(self, message: Dict) -> bool:
        """Determine if the message is requesting code review."""
        content = message.get("content", "").lower()
        review_keywords = {"review", "check", "analyze", "improve", "optimize"}
        return any(keyword in content for keyword in review_keywords)

    async def _handle_code_execution(self, message: Dict) -> str:
        """Handle code execution requests safely using UserProxyAgent."""
        try:
            # Extract code from message
            code = self._extract_code(message["content"])
            if not code:
                return "No executable code found in the message."

            # Prepare execution environment
            container_config = self._prepare_container_config()
            
            # Execute code through UserProxyAgent
            result = await self.executor.execute_code(
                code,
                work_dir=self.workspace_dir,
                use_docker=True,
                container_config=container_config
            )

            return self._format_execution_result(result)

        except Exception as e:
            logger.error(f"Code execution error: {str(e)}")
            return f"Error executing code: {str(e)}"

    async def _handle_code_review(self, message: Dict) -> str:
        """Handle code review requests."""
        try:
            code = self._extract_code(message["content"])
            if not code:
                return "No code found to review."

            # Analyze code using LLM
            review_prompt = self._create_review_prompt(code)
            review_result = await self.generate_response(review_prompt)

            return review_result

        except Exception as e:
            logger.error(f"Code review error: {str(e)}")
            return f"Error reviewing code: {str(e)}"

    def _extract_code(self, content: str) -> Optional[str]:
        """Extract code blocks from message content."""
        import re
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
        return code_blocks[0] if code_blocks else None

    def _prepare_container_config(self) -> Dict:
        """Prepare Docker container configuration for code execution."""
        return {
            "image": "python:3.9-slim",
            "command": "python",
            "volumes": {
                str(self.workspace_dir.absolute()): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            "working_dir": "/workspace",
            "network_disabled": True,
            "mem_limit": "512m",
            "cpu_period": 100000,
            "cpu_quota": 50000
        }

    def _format_execution_result(self, result: Dict) -> str:
        """Format the execution result for display."""
        output = ["Code Execution Result:"]
        
        if "output" in result:
            output.append("\nOutput:")
            output.append(result["output"])
        
        if "error" in result:
            output.append("\nErrors:")
            output.append(result["error"])
        
        if "execution_time" in result:
            output.append(f"\nExecution Time: {result['execution_time']:.2f} seconds")

        return "\n".join(output)

    def _create_review_prompt(self, code: str) -> str:
        """Create a prompt for code review analysis."""
        return f"""Please review the following code focusing on:
        1. Code quality and best practices
        2. Security considerations
        3. Performance optimizations
        4. Maintainability improvements
        5. Potential bugs or issues

        Code to review:
        ```python
        {code}
        ```

        Provide specific recommendations and explanations for each point."""

    async def generate_response(self, prompt: str) -> str:
        """Generate a response using the configured LLM."""
        response = await super().generate_response(prompt)
        return response

    def cleanup(self):
        """Cleanup resources when done."""
        if self.docker_client:
            self.docker_client.close()
            
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
            llm_config=config.llm_config
        )

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
            llm_config=config.llm_config
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
            llm_config=config.llm_config
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
            llm_config=config.llm_config
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
            llm_config=config.llm_config
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

    def execute_group_task(
        self, 
        task_description: str, 
        agents: List[AssistantAgent],
        max_rounds: int = 10
    ) -> Dict:
        """Execute a task using a group of agents"""
        try:
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
                max_round=max_rounds
            )
            
            # Create chat manager
            manager = GroupChatManager(
                groupchat=groupchat,
                llm_config=self.config.llm_config,
                system_message=f"""Coordinate the completion of this task:
                {task_description}
                
                Ensure each agent contributes according to their expertise.
                The project manager should coordinate the overall effort.
                Verify results before marking the task as complete."""
            )
            
            # Start the group chat
            chat_result = agents[0].initiate_chat(
                manager,
                message=task_description
            )
            
            return {
                "success": True,
                "chat_history": groupchat.messages,
                "result": chat_result
            }
            
        except Exception as e:
            logger.error(f"Error during group task execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "chat_history": []
            }

    def execute_sequential_tasks(
        self, 
        tasks: List[Dict],
        required_agents: List[str]
    ) -> List[Dict]:
        """Execute a sequence of related tasks"""
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