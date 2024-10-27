from typing import Dict, List, Optional
import queue
import uuid
from datetime import datetime
from .config import SystemConfig

class TeamConfiguration:
    """Manages team compositions and agent relationships for workflows"""
    def __init__(self, monitor):
        self.monitor = monitor
        self.workflow_id = str(uuid.uuid4())
        
        # Team templates
        self.research_team_template = {
            "agents": [
                {"role": "Research", "name": "Primary Researcher", "capabilities": ["data_analysis", "paper_review"]},
                {"role": "Code", "name": "Research Assistant", "capabilities": ["implementation", "testing"]},
                {"role": "QA", "name": "Review Specialist", "capabilities": ["verification", "validation"]},
            ]
        }
        
        self.development_team_template = {
            "agents": [
                {"role": "Code", "name": "Lead Developer", "capabilities": ["architecture", "implementation"]},
                {"role": "QA", "name": "Test Engineer", "capabilities": ["testing", "quality"]},
                {"role": "PM", "name": "Project Manager", "capabilities": ["coordination", "planning"]},
                {"role": "Viz", "name": "UI Specialist", "capabilities": ["visualization", "design"]}
            ]
        }

    def create_research_team(self) -> Dict:
        """Create a research-focused team configuration"""
        team_config = self._create_team_from_template(self.research_team_template)
        
        # Set up team-specific configurations
        team_config["type"] = "research"
        team_config["workflow_rules"] = {
            "review_required": True,
            "validation_steps": ["peer_review", "result_validation"],
            "output_formats": ["paper", "code", "data"]
        }
        
        return team_config

    def create_development_team(self) -> Dict:
        """Create a development-focused team configuration"""
        team_config = self._create_team_from_template(self.development_team_template)
        
        # Set up team-specific configurations
        team_config["type"] = "development"
        team_config["workflow_rules"] = {
            "code_review_required": True,
            "testing_required": True,
            "deployment_steps": ["test", "stage", "prod"]
        }
        
        return team_config

    def _create_team_from_template(self, template: Dict) -> Dict:
        """Create a team configuration from a template"""
        team_config = {
            "id": self.workflow_id,
            "created_at": datetime.now().isoformat(),
            "status": "initializing",
            "agents": [],
            "connections": [],
            "metrics": {
                "tasks_completed": 0,
                "messages_processed": 0,
                "active_time": 0
            }
        }
        
        # Create agents from template
        for agent_spec in template["agents"]:
            agent_id = f"{agent_spec['role']}_{uuid.uuid4().hex[:8]}"
            agent = {
                "id": agent_id,
                "name": agent_spec["name"],
                "role": agent_spec["role"],
                "capabilities": agent_spec["capabilities"],
                "status": "ready",
                "position": (0, 0)  # Will be set by node editor
            }
            team_config["agents"].append(agent)
        
        return team_config

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
        """Start a workflow's execution"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Get team configuration
        team_config = workflow.get('team_config')
        if not team_config:
            raise ValueError(f"No team configuration for workflow: {workflow_id}")
        
        # Update workflow status
        workflow['status'] = 'running'
        workflow['agents'] = [
            {'name': agent.name, 'role': agent.__class__.__name__}
            for agent in team_config.values()
        ]
        
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