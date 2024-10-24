# src/task_decomposition.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from .agents.specialized import TeamManager
from autogen import AssistantAgent

@dataclass
class SubTask:
    """Represents a decomposed subtask"""
    description: str
    required_agents: List[str]
    dependencies: List[str]  # IDs of tasks that must be completed first
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    id: Optional[str] = None

# src/task_decomposition.py

class TaskDecomposer:
    """Breaks down complex tasks into manageable subtasks"""
    
    def __init__(self, config, team_manager: TeamManager):
        self.config = config
        self.team_manager = team_manager
        
        # Create the decomposer agent
        self.decomposer = AssistantAgent(
            name="task_decomposer",
            system_message="""You are an expert at breaking down complex tasks into smaller, manageable subtasks.
            For each subtask, provide:
            1. A clear description
            2. Required agent types (must include at least one of: research, code, viz, qa, pm)
            3. Any dependencies on other subtasks
            
            Format each subtask as:
            ### Subtask [number]: [title]
            Description: [detailed description]
            Required Agents: [comma-separated list of required agents]
            Dependencies: [comma-separated list of subtask numbers or 'none']
            
            Example:
            ### Subtask 1: Research Latest Papers
            Description: Gather and analyze recent research papers on the topic
            Required Agents: research, qa
            Dependencies: none
            
            Available agent types:
            - research: For gathering and analyzing information
            - code: For programming and technical tasks
            - viz: For data visualization and presentation
            - qa: For quality assurance and testing
            - pm: For project management and coordination""",
            llm_config={"config_list": config.llm_config_list}
        )
    
    def decompose_task(self, task: str) -> List[SubTask]:
        """Decompose a complex task into subtasks"""
        
        # Ask the decomposer to analyze the task
        response = self.decomposer.generate_reply(
            messages=[{
                "role": "user",
                "content": f"""Please break down this task into subtasks:
                {task}
                
                Follow the format specified in your instructions, ensuring each subtask
                has required agents and dependencies clearly specified."""
            }]
        )
        
        # Parse the response into SubTask objects
        subtasks = self._parse_decomposition(response)
        
        # Validate subtasks
        self._validate_subtasks(subtasks)
        
        return subtasks
    
    def _parse_decomposition(self, response: str) -> List[SubTask]:
        """Parse the decomposer's response into SubTask objects"""
        subtasks = []
        current_subtask = None
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('### Subtask'):
                # Save previous subtask if exists
                if current_subtask and current_subtask.description:
                    subtasks.append(current_subtask)
                
                # Create new subtask
                current_subtask = SubTask(
                    description="",
                    required_agents=[],
                    dependencies=[],
                    id=f"task_{len(subtasks)}"
                )
                # Add title to description
                current_subtask.description = line.split(':', 1)[1].strip() + "\n"
                
            elif current_subtask:
                if line.lower().startswith('description:'):
                    desc = line.split(':', 1)[1].strip()
                    current_subtask.description += desc + "\n"
                    
                elif line.lower().startswith('required agents:'):
                    agents = line.split(':', 1)[1].strip()
                    current_subtask.required_agents = [
                        a.strip().lower() for a in agents.split(',')
                        if a.strip()
                    ]
                    
                elif line.lower().startswith('dependencies:'):
                    deps = line.split(':', 1)[1].strip()
                    if deps.lower() != 'none':
                        current_subtask.dependencies = [
                            f"task_{int(d.strip())-1}" 
                            for d in deps.split(',')
                            if d.strip().isdigit()
                        ]
                
                else:
                    # Add to description
                    current_subtask.description += line + "\n"
        
        # Add the last subtask
        if current_subtask and current_subtask.description:
            subtasks.append(current_subtask)
            
        return subtasks
    
    def _validate_subtasks(self, subtasks: List[SubTask]):
        """Validate that subtasks are properly formed"""
        for task in subtasks:
            # Ensure each task has at least one agent
            if not task.required_agents:
                raise ValueError(f"Task {task.id} has no required agents specified")
            
            # Validate agent types
            valid_agents = {'research', 'code', 'viz', 'qa', 'pm'}
            invalid_agents = set(task.required_agents) - valid_agents
            if invalid_agents:
                raise ValueError(f"Task {task.id} has invalid agent types: {invalid_agents}")
            
            # Validate dependencies
            for dep in task.dependencies:
                if not any(t.id == dep for t in subtasks):
                    raise ValueError(f"Task {task.id} has invalid dependency: {dep}")


class TaskExecutor:
    """Executes decomposed tasks using the appropriate agents"""
    
    def __init__(self, team_manager: TeamManager):
        self.team_manager = team_manager
        self.completed_tasks: Dict[str, SubTask] = {}
        
    def execute_subtasks(self, subtasks: List[SubTask]) -> Dict[str, Dict]:
        """Execute a list of subtasks in the correct order"""
        results = {}
        
        while subtasks:
            # Find tasks that can be executed (all dependencies met)
            ready_tasks = [
                task for task in subtasks
                if all(dep in self.completed_tasks for dep in task.dependencies)
            ]
            
            if not ready_tasks:
                raise Exception("Dependency cycle detected or no tasks ready")
            
            # Execute ready tasks
            for task in ready_tasks:
                print(f"\nExecuting task: {task.description}")
                
                # Get the required agents
                agents = [
                    self.team_manager.get_agent(role)
                    for role in task.required_agents
                    if self.team_manager.get_agent(role) is not None
                ]
                
                try:
                    # Execute the task with the group
                    result = self.team_manager.execute_group_task(
                        task_description=task.description,
                        agents=agents
                    )
                    
                    # Store the result
                    if result["success"]:
                        task.status = "completed"
                        self.completed_tasks[task.id] = task
                    else:
                        task.status = "failed"
                    
                    results[task.id] = {
                        "status": task.status,
                        "result": result,
                        "description": task.description,
                        "agents": [agent.name for agent in agents]
                    }
                    
                except Exception as e:
                    print(f"Task failed: {str(e)}")
                    task.status = "failed"
                    results[task.id] = {
                        "status": "failed",
                        "error": str(e),
                        "description": task.description,
                        "agents": [agent.name for agent in agents]
                    }
                
                # Remove completed/failed task from the list
                subtasks.remove(task)
                
                # Print progress
                print(f"Task {task.id} {task.status}")
        
        return results
    
    
def decompose_and_execute(
    task: str,
    config,
    team_manager: TeamManager
) -> Dict[str, Dict]:
    """Main function to decompose and execute a complex task"""
    
    # Create decomposer and executor
    decomposer = TaskDecomposer(config, team_manager)
    executor = TaskExecutor(team_manager)
    
    try:
        # Decompose the task
        print("Decomposing task...")
        subtasks = decomposer.decompose_task(task)
        
        # Log the decomposition
        print("\nTask Decomposition:")
        for task in subtasks:
            print(f"\nTask {task.id}:")
            print(f"Description: {task.description.strip()}")
            print(f"Required Agents: {', '.join(task.required_agents)}")
            print(f"Dependencies: {', '.join(task.dependencies) if task.dependencies else 'none'}")
        
        # Execute subtasks
        print("\nExecuting subtasks...")
        results = executor.execute_subtasks(subtasks)
        
        return results
        
    except Exception as e:
        print(f"\nError in task decomposition/execution: {str(e)}")
        return {"error": str(e)}