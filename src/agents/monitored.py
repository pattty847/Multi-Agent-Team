from autogen import ConversableAgent, GroupChat, GroupChatManager
from typing import Dict, List
import uuid
from datetime import datetime

class MonitoredAgent(ConversableAgent):
    def __init__(self, name: str, role: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.role = role
        self.workflow_id = None
        self.monitor = None

    def send(self, message, recipient, request_reply=True, silent=False):
        """Override send to log interactions"""
        if self.monitor and self.workflow_id:
            interaction = {
                'from': self.name,
                'to': recipient.name,
                'timestamp': datetime.utcnow().isoformat(),
                'message': message
            }
            self.monitor.log_interaction(self.workflow_id, interaction)
        
        return super().send(message, recipient, request_reply, silent)

class TeamConfiguration:
    def __init__(self, monitor):
        self.monitor = monitor
        self.workflow_id = str(uuid.uuid4())

    def create_research_team(self) -> GroupChat:
        """Create a research-focused team configuration"""
        
        # Create specialized agents
        researcher = MonitoredAgent(
            name="Researcher",
            role="Primary Researcher",
            system_message="You are a thorough researcher who excels at breaking down complex topics.",
            monitor=self.monitor
        )

        analyst = MonitoredAgent(
            name="Analyst",
            role="Data Analyst",
            system_message="You analyze and interpret data, creating clear visualizations and insights.",
            monitor=self.monitor
        )

        writer = MonitoredAgent(
            name="Writer",
            role="Technical Writer",
            system_message="You translate complex technical information into clear, accessible content.",
            monitor=self.monitor
        )

        reviewer = MonitoredAgent(
            name="Reviewer",
            role="Quality Reviewer",
            system_message="You review outputs for accuracy, clarity, and completeness.",
            monitor=self.monitor
        )

        # Set workflow ID for all agents
        for agent in [researcher, analyst, writer, reviewer]:
            agent.workflow_id = self.workflow_id

        # Create group chat with specific interaction rules
        groupchat = GroupChat(
            agents=[researcher, analyst, writer, reviewer],
            messages=[],
            max_round=50,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
            speaker_transitions_type="allowed",
            allowed_or_disallowed_speaker_transitions={
                researcher: [analyst, writer],
                analyst: [writer, reviewer],
                writer: [reviewer, researcher],
                reviewer: [researcher, analyst]
            }
        )

        # Register the workflow with the monitor
        self.monitor.register_workflow(
            self.workflow_id,
            {
                'agents': [
                    {'name': agent.name, 'role': agent.role}
                    for agent in groupchat.agents
                ],
                'interactions': []
            }
        )

        return groupchat

    def create_development_team(self) -> GroupChat:
        """Create a software development-focused team configuration"""
        
        # Create specialized agents
        architect = MonitoredAgent(
            name="Architect",
            role="System Architect",
            system_message="You design high-level software architecture and make key technical decisions.",
            monitor=self.monitor
        )

        developer = MonitoredAgent(
            name="Developer",
            role="Software Developer",
            system_message="You implement solutions following best practices and design patterns.",
            monitor=self.monitor
        )

        tester = MonitoredAgent(
            name="Tester",
            role="QA Engineer",
            system_message="You ensure code quality through thorough testing and validation.",
            monitor=self.monitor
        )

        devops = MonitoredAgent(
            name="DevOps",
            role="DevOps Engineer",
            system_message="You handle deployment, infrastructure, and operational concerns.",
            monitor=self.monitor
        )

        # Set workflow ID for all agents
        for agent in [architect, developer, tester, devops]:
            agent.workflow_id = self.workflow_id

        # Create group chat with specific interaction rules
        groupchat = GroupChat(
            agents=[architect, developer, tester, devops],
            messages=[],
            max_round=50,
            speaker_selection_method="round_robin",
            allow_repeat_speaker=False,
            speaker_transitions_type="allowed",
            allowed_or_disallowed_speaker_transitions={
                architect: [developer, devops],
                developer: [tester, architect],
                tester: [developer, devops],
                devops: [architect, developer]
            }
        )

        # Register the workflow with the monitor
        self.monitor.register_workflow(
            self.workflow_id,
            {
                'agents': [
                    {'name': agent.name, 'role': agent.role}
                    for agent in groupchat.agents
                ],
                'interactions': []
            }
        )

        return groupchat