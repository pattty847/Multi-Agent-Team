# src/team_tasks.py
from typing import List, Dict

from src.config.system_config import SystemConfig
from .agents.specialized import TeamManager
from autogen import GroupChat, GroupChatManager

class GroupTaskManager:
    """Manages group tasks and agent interactions"""
    def __init__(self, config: SystemConfig, executor):
        self.team_manager = TeamManager(config, executor)
        self.config = config
        
    def create_group_chat(self, agents: List[str], task: str) -> tuple:
        """Create a group chat with specified agents"""
        # Get requested agents
        selected_agents = [
            self.team_manager.get_agent(role)
            for role in agents
            if self.team_manager.get_agent(role)
        ]
        
        # Create group chat with updated configuration based on latest AutoGen API
        group_chat = GroupChat(
            agents=selected_agents,
            messages=[],
            max_round=50,
            send_introductions=True,  # Agents will introduce themselves
        )
        
        # Create chat manager with updated configuration
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config={"config_list": self.config.llm_config_list},
            system_message="""You are a group chat manager coordinating a team of AI agents.
            Help them work together effectively to solve the given task.
            Ensure each agent contributes according to their expertise.""",
        )
        
        return manager, group_chat

    def format_task(self, task: str) -> str:
        """Format task message with clear instructions"""
        return f"""
        TASK DESCRIPTION:
        {task}
        
        COLLABORATION GUIDELINES:
        1. Project Manager (pm) should coordinate the overall effort
        2. Each specialist should contribute based on their expertise
        3. Maintain clear communication and documentation
        4. Verify results and quality at each step
        
        EXPECTED OUTCOMES:
        1. Clear documentation of the process
        2. Quality-assured results
        3. Proper testing and validation
        4. Performance considerations
        
        Please begin with task planning and proceed with execution.
        """
    
    def execute_task(self, task: str, required_agents: List[str]) -> Dict:
        """Execute a task using the specified agents"""
        try:
            # Create group chat
            manager, chat = self.create_group_chat(required_agents, task)
            
            # Format task message
            formatted_task = self.format_task(task)
            
            # Get the first agent to initiate the chat
            initiator = chat.agents[0]
            
            # Start the group chat with the first agent as initiator
            chat_result = initiator.initiate_chat(
                recipient=manager,
                message=formatted_task,
            )
            
            return {
                "result": chat_result,
                "chat_history": chat.messages,
                "participants": [agent.name for agent in chat.agents]
            }
            
        except Exception as e:
            print(f"\nError during task execution: {str(e)}")
            return {
                "error": str(e),
                "participants": [agent.name for agent in chat.agents] if 'chat' in locals() else [],
                "status": "failed"
            }