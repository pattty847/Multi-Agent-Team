from typing import Dict, List, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
import logging
from datetime import datetime
import asyncio
import networkx as nx
from collections import defaultdict

from autogen import ConversableAgent
from autogen import Agent
from autogen import GroupChat, GroupChatManager
from .memory_store import VectorMemoryStore  # Hypothetical memory store

logger = logging.getLogger(__name__)

@dataclass
class TeamRole:
    """Defines a role that can be assigned to agents"""
    name: str
    capabilities: Set[str]
    description: str
    primary_agent: Optional[Agent] = None
    backup_agents: List[Agent] = field(default_factory=list)

@dataclass
class WorkflowEvent:
    """Represents a significant event in the workflow for the ledger"""
    timestamp: datetime
    event_type: str
    workflow_id: str
    task_id: Optional[str]
    agent_id: Optional[str]
    details: Dict

@dataclass
class Workflow:
    """Represents a sequence of tasks with their dependencies"""
    id: str
    tasks: List[Dict]
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    status: str = "pending"
    assigned_roles: Dict[str, str] = field(default_factory=dict)

class WorkflowLedger:
    """Maintains a comprehensive record of workflow execution and decisions"""
    
    def __init__(self, vector_store: VectorMemoryStore):
        self.events: List[WorkflowEvent] = []
        self.agent_memories: Dict[str, Dict] = defaultdict(dict)
        self.vector_store = vector_store
        self.task_graph = nx.DiGraph()
        
    async def record_event(self, event: WorkflowEvent):
        """Record a new event and update relevant metrics"""
        self.events.append(event)
        
        # Update agent metrics if applicable
        if event.agent_id:
            self._update_agent_metrics(event)
            
        # Store in vector database for future reference
        await self.vector_store.store(
            f"{event.workflow_id}_{event.timestamp.isoformat()}",
            event.details
        )
    
    def _update_agent_metrics(self, event: WorkflowEvent):
        """Update agent performance metrics based on event"""
        metrics = self.agent_memories[event.agent_id]
        
        if event.event_type == "task_complete":
            metrics["successful_tasks"] = metrics.get("successful_tasks", 0) + 1
        elif event.event_type == "task_failed":
            metrics["failed_tasks"] = metrics.get("failed_tasks", 0) + 1
            
        # Calculate success rate
        total_tasks = metrics.get("successful_tasks", 0) + metrics.get("failed_tasks", 0)
        if total_tasks > 0:
            metrics["success_rate"] = metrics.get("successful_tasks", 0) / total_tasks

class UnifiedTeamOrchestrator(GroupChatManager):
    """
    Enhanced GroupChatManager that combines dynamic team orchestration with 
    sophisticated ledger and memory systems.
    """
    
    def __init__(
        self,
        team_name: str,
        roles: List[TeamRole],
        agents: List[Agent],
        vector_store: VectorMemoryStore,
        admin_name: str = "Team Lead",
        max_round: int = 50,
        task_decomposition_prompt: Optional[str] = None,
        role_selection_prompt: Optional[str] = None
    ):
        # Initialize management agents first
        self.task_planner = self._create_task_planner()
        self.role_manager = self._create_role_manager()
        self.workflow_monitor = self._create_workflow_monitor()
        self.dependency_validator = self._create_dependency_validator()
        self.compliance_monitor = self._create_compliance_monitor()
        
        # Combine all agents
        all_agents = [
            self.task_planner,
            self.role_manager,
            self.workflow_monitor,
            self.dependency_validator,
            self.compliance_monitor
        ] + agents
        
        # Initialize GroupChat with enhanced selection method
        groupchat = GroupChat(
            agents=all_agents,
            messages=[],
            max_round=max_round,
            admin_name=admin_name,
            speaker_selection_method=self._dynamic_speaker_selection,
            allow_repeat_speaker=True
        )
        
        # Initialize GroupChatManager parent
        super().__init__(
            groupchat=groupchat,
            name=admin_name,
            system_message=f"Orchestrating team: {team_name}"
        )
        
        # Initialize own attributes
        self.team_name = team_name
        self.roles = {role.name: role for role in roles}
        self.ledger = WorkflowLedger(vector_store)
        self.workflows: Dict[str, Workflow] = {}
        
        # Store prompts
        self.task_decomposition_prompt = task_decomposition_prompt or self._default_task_prompt()
        self.role_selection_prompt = role_selection_prompt or self._default_role_prompt()
    
    def _create_task_planner(self) -> ConversableAgent:
        """Creates the task planning specialist agent"""
        return ConversableAgent(
            name="TaskPlanner",
            system_message="""You are a Task Planning Specialist who:
            1. Breaks down complex tasks into manageable subtasks
            2. Identifies dependencies between tasks
            3. Suggests optimal task sequences
            4. Estimates resource requirements
            Only respond with actionable task breakdowns.""",
            llm_config={"temperature": 0.2}
        )

    def _create_role_manager(self) -> ConversableAgent:
        """Creates the role management specialist agent"""
        return ConversableAgent(
            name="RoleManager",
            system_message="""You are a Role Management Specialist who:
            1. Matches agent capabilities to role requirements
            2. Suggests role reassignments based on performance
            3. Identifies skill gaps in the team
            4. Maintains optimal role coverage
            Focus on maximizing team effectiveness through role optimization.""",
            llm_config={"temperature": 0.3}
        )

    def _create_workflow_monitor(self) -> ConversableAgent:
        """Creates the workflow monitoring specialist agent"""
        return ConversableAgent(
            name="WorkflowMonitor",
            system_message="""You are a Workflow Monitoring Specialist who:
            1. Tracks progress of ongoing tasks
            2. Identifies bottlenecks and inefficiencies
            3. Suggests process improvements
            4. Monitors team communication patterns
            Provide concise status updates and actionable improvements.""",
            llm_config={"temperature": 0.2}
        )

    def _create_dependency_validator(self) -> ConversableAgent:
        """Creates the dependency validation specialist agent"""
        return ConversableAgent(
            name="DependencyValidator",
            system_message="""You are a Dependency Validation Specialist who:
            1. Validates task dependencies before execution
            2. Ensures prerequisite tasks are properly completed
            3. Identifies potential dependency conflicts
            4. Suggests optimal task ordering
            Focus on maintaining workflow integrity through proper dependency management.""",
            llm_config={"temperature": 0.2}
        )

    def _create_compliance_monitor(self) -> ConversableAgent:
        """Creates the compliance monitoring specialist agent"""
        return ConversableAgent(
            name="ComplianceMonitor",
            system_message="""You are a Compliance Monitoring Specialist who:
            1. Ensures actions meet safety and compliance requirements
            2. Validates data handling procedures
            3. Monitors for potential risks
            4. Maintains audit trails of critical decisions
            Focus on maintaining system integrity and safety.""",
            llm_config={"temperature": 0.2}
        )

    async def _dynamic_speaker_selection(
        self,
        last_speaker: Agent,
        groupchat: GroupChat
    ) -> Union[Agent, str, None]:
        """Smart speaker selection based on context and current workflow state"""
        current_message = groupchat.messages[-1] if groupchat.messages else None
        if not current_message:
            return "round_robin"

        content = current_message.get("content", "").lower()

        # Route to appropriate specialist based on content
        if "task" in content or "breakdown" in content:
            return self.task_planner
        elif "role" in content or "assignment" in content:
            return self.role_manager
        elif "status" in content or "progress" in content:
            return self.workflow_monitor
        elif "dependency" in content or "prerequisite" in content:
            return self.dependency_validator
        elif "compliance" in content or "safety" in content:
            return self.compliance_monitor
            
        return "auto"

    async def initiate_workflow(self, objective: str) -> str:
        """Initiate a new workflow with full monitoring and validation"""
        workflow_id = f"workflow_{len(self.workflows) + 1}"
        
        # Record workflow initiation
        await self.ledger.record_event(
            WorkflowEvent(
                timestamp=datetime.now(),
                event_type="workflow_start",
                workflow_id=workflow_id,
                task_id=None,
                agent_id=None,
                details={"objective": objective}
            )
        )
        
        try:
            # Get task breakdown from task planner
            tasks = await self._get_task_breakdown(objective)
            
            # Validate dependencies
            await self._validate_dependencies(tasks)
            
            # Get role assignments
            role_assignments = await self._assign_roles(tasks)
            
            # Create workflow
            workflow = Workflow(
                id=workflow_id,
                tasks=tasks,
                assigned_roles=role_assignments
            )
            self.workflows[workflow_id] = workflow
            
            # Begin execution
            asyncio.create_task(self._execute_workflow(workflow))
            
            return workflow_id
            
        except Exception as e:
            await self.ledger.record_event(
                WorkflowEvent(
                    timestamp=datetime.now(),
                    event_type="workflow_error",
                    workflow_id=workflow_id,
                    task_id=None,
                    agent_id=None,
                    details={"error": str(e)}
                )
            )
            raise

    async def _execute_workflow(self, workflow: Workflow):
        """Execute workflow with monitoring and adaptability"""
        try:
            workflow.status = "in_progress"
            
            for task in workflow.tasks:
                if not await self._are_dependencies_met(task, workflow):
                    continue
                    
                # Get assigned agent
                role_name = workflow.assigned_roles.get(task["id"])
                if not role_name:
                    continue
                    
                role = self.roles[role_name]
                agent = role.primary_agent
                
                if not agent:
                    continue
                    
                # Execute task with monitoring
                await self._execute_task(task, agent, workflow.id)
                
                # Get workflow monitor's assessment
                await self._assess_workflow_progress(workflow)
                
            workflow.status = "completed"
            
        except Exception as e:
            workflow.status = "failed"
            logger.error(f"Workflow {workflow.id} failed: {str(e)}")
            raise

    def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get detailed status of a specific workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
            
        return {
            "id": workflow.id,
            "status": workflow.status,
            "tasks_completed": len([t for t in workflow.tasks if t.get("status") == "completed"]),
            "tasks_total": len(workflow.tasks),
            "current_assignments": workflow.assigned_roles,
            "agent_metrics": {
                agent_id: self.ledger.agent_memories[agent_id]
                for agent_id in self.ledger.agent_memories
            }
        }

    def _default_task_prompt(self) -> str:
        """Default prompt for task decomposition"""
        return """Please break down this objective into specific tasks. For each task, provide:
        1. Task ID
        2. Description
        3. Required capabilities
        4. Expected dependencies
        5. Success criteria
        
        Format as a JSON structure."""

    def _default_role_prompt(self) -> str:
        """Default prompt for role selection"""
        return """Given these tasks and available roles, suggest the optimal role assignment for each task.
        Consider:
        1. Role capabilities vs task requirements
        2. Current workload and availability
        3. Task dependencies and sequence
        
        Provide assignments as task_id: role_name pairs."""