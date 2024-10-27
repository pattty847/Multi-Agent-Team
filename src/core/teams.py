from datetime import datetime
from typing import Dict, List
import uuid


class TeamConfiguration:
    """Manages team compositions and agent relationships for workflows"""
    def __init__(self):
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
    
    def get_team_types_and_roles(self) -> Dict[str, List[str]]:
        """Get a dictionary of team types and their roles."""
        return {
            "research": [agent["role"] for agent in self.research_team_template["agents"]],
            "development": [agent["role"] for agent in self.development_team_template["agents"]]
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