from typing import Dict, List, Optional
import queue
import uuid
from datetime import datetime

from src.core.teams import TeamConfiguration
from ..config.agent_config import SystemConfig

class WorkflowManager:
    """Manages agent workflows and team coordination"""
    
    def __init__(self, config: SystemConfig, message_queue: queue.Queue):
        self.config = config
        self.message_queue = message_queue
        self.active_workflows: Dict[str, Dict] = {}
    
    def create_workflow(self, workflow_type: str, task: str) -> str:
        """Create a new workflow of specified type"""
        workflow_id = str(uuid.uuid4())
        
        # Create workflow data structure
        workflow_data = {
            'id': workflow_id,
            'type': workflow_type,
            'status': 'initialized',
            'task': task,
            'created_at': datetime.now().isoformat(),
            'agents': [],  # Will be populated when workflow starts
            'interactions': [],
            'team_config': None  # Will be set by main system
        }
        
        self.active_workflows[workflow_id] = workflow_data
        
        # Notify monitor
        if self.message_queue:
            self.message_queue.put({
                'type': 'new_workflow',
                'workflow_id': workflow_id,
                'data': workflow_data
            })
        
        return workflow_id
    
    def start_workflow(self, workflow_id: str) -> None:
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Update workflow status
        workflow['status'] = 'running'
        
        # Use agents from team configuration
        team_config = workflow.get('team_config')
        if team_config:
            workflow['agents'] = team_config["agents"]
        else:
            # Handle the case where team_config is missing
            pass
        
        self._update_workflow(workflow_id)
        
        # Start initial interaction
        self._log_interaction(workflow_id, {
            'from': 'system',
            'to': 'all',
            'message': f"Starting workflow: {workflow['task']}",
            'timestamp': datetime.now().isoformat()
        })

    
    def _log_interaction(self, workflow_id: str, interaction: Dict) -> None:
        """Log an interaction in the workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow['interactions'].append(interaction)
            self._update_workflow(workflow_id)
            
            # Send message to monitor
            if self.message_queue:
                self.message_queue.put({
                    'type': 'message',
                    'content': f"{interaction['from']} → {interaction['to']}: {interaction['message'][:100]}..."
                })
    
    def _update_workflow(self, workflow_id: str) -> None:
        """Send workflow update to monitor"""
        if workflow_id in self.active_workflows and self.message_queue:
            self.message_queue.put({
                'type': 'workflow_update',
                'workflow_id': workflow_id,
                'data': self.active_workflows[workflow_id]
            })