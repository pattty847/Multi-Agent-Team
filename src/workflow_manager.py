from typing import Dict, List, Optional
import queue
import uuid
from datetime import datetime
from .agents.monitored import MonitoredAgent, TeamConfiguration
from .config import SystemConfig

class WorkflowManager:
    """Manages agent workflows and team coordination"""
    
    def __init__(self, config: SystemConfig, message_queue: queue.Queue):
        self.config = config
        self.message_queue = message_queue  # Shared with monitor
        self.active_workflows: Dict[str, Dict] = {}
        self.agent_teams: Dict[str, TeamConfiguration] = {}
    
    def create_workflow(self, workflow_type: str, task: str) -> str:
        """Create a new workflow of specified type"""
        workflow_id = str(uuid.uuid4())
        
        # Create appropriate team configuration
        team_config = TeamConfiguration(self)
        
        if workflow_type == "research":
            team = team_config.create_research_team()
        elif workflow_type == "development":
            team = team_config.create_development_team()
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Store team configuration
        self.agent_teams[workflow_id] = team_config
        
        # Create workflow data
        workflow_data = {
            'id': workflow_id,
            'type': workflow_type,
            'status': 'initialized',
            'task': task,
            'created_at': datetime.now().isoformat(),
            'agents': [
                {'name': agent.name, 'role': agent.role}
                for agent in team.agents
            ],
            'interactions': []
        }
        
        self.active_workflows[workflow_id] = workflow_data
        
        # Notify monitor
        self.message_queue.put({
            'type': 'new_workflow',
            'workflow_id': workflow_id,
            'data': workflow_data
        })
        
        return workflow_id
    
    def start_workflow(self, workflow_id: str) -> None:
        """Start a workflow's execution"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        team = self.agent_teams.get(workflow_id)
        if not team:
            raise ValueError(f"Team not found for workflow: {workflow_id}")
        
        # Update status
        workflow['status'] = 'running'
        self._update_workflow(workflow_id)
        
        # Start the team chat
        team_chat = team.groupchat
        initial_message = f"""Task Description:
        {workflow['task']}
        
        Please work together to complete this task. Each agent should contribute
        based on their expertise."""
        
        # Get first agent to start
        first_agent = team_chat.agents[0]
        first_agent.initiate_chat(
            team_chat.manager,
            message=initial_message
        )
    
    def stop_workflow(self, workflow_id: str) -> None:
        """Stop a workflow's execution"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Update status
        workflow['status'] = 'stopped'
        self._update_workflow(workflow_id)
        
        # Cleanup team
        if workflow_id in self.agent_teams:
            del self.agent_teams[workflow_id]
    
    def log_interaction(self, workflow_id: str, interaction: Dict) -> None:
        """Log an interaction between agents"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return
        
        workflow['interactions'].append(interaction)
        self._update_workflow(workflow_id)
        
        # Also send as message for the log
        self.message_queue.put({
            'type': 'message',
            'content': f"{interaction['from']} → {interaction['to']}: {interaction['message'][:100]}..."
        })
    
    def _update_workflow(self, workflow_id: str) -> None:
        """Send workflow update to monitor"""
        if workflow_id in self.active_workflows:
            self.message_queue.put({
                'type': 'workflow_update',
                'workflow_id': workflow_id,
                'data': self.active_workflows[workflow_id]
            })
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get current status of a workflow"""
        return self.active_workflows.get(workflow_id)