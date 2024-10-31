# components/agent_list.py
from typing import Dict
import dearpygui.dearpygui as dpg

from src.ui.state.agent import AgentState

class AgentListView:
    def __init__(self, parent_id: int):
        self.parent_id = parent_id
        self.selected_agent_id = None
        self.agents = {}
        
    def setup(self):
        with dpg.child_window(parent=self.parent_id):
            # Workflow Control Section
            with dpg.collapsing_header(label="Workflow Control", default_open=True):
                dpg.add_combo(
                    label="Workflow Type",
                    items=["Research", "Code", "Viz", "QA", "PM"],
                    width=-1
                )
                dpg.add_input_text(
                    label="Task Description",
                    multiline=True,
                    height=100,
                    width=-1
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Start New Workflow")
                    dpg.add_button(label="Stop Selected")

            # Agent List Section
            with dpg.collapsing_header(label="Agent List", default_open=True):
                dpg.add_text("All")  # Default filter view
                dpg.add_combo(
                    label="Filter by Type",
                    items=["All", "Research", "Code", "Viz", "QA", "PM"],
                    default_value="All",
                    callback=self._filter_agents,
                    width=-1
                )
                
                # Simple list of agents (more compact)
                dpg.add_listbox(
                    tag="agent_list",
                    items=[],
                    num_items=8,
                    callback=self._on_agent_selected,
                    width=-1
                )

    def _create_agent_details_window(self):
        """Create detailed agent info window like in the reference"""
        with dpg.window(
            label="Agent Details",
            tag="agent_details_window",
            pos=(100, 100),
            width=300,
            height=400,
            collapsed=False
        ):
            with dpg.collapsing_header(label="Basic Info", default_open=True):
                dpg.add_text("Agent ID: ", tag="details_agent_id")
                dpg.add_text("Type: ", tag="details_type")
                dpg.add_text("Role: ", tag="details_role")
                dpg.add_text("Status: ", tag="details_status")

            with dpg.collapsing_header(label="Performance", default_open=True):
                dpg.add_text("CPU Usage: ", tag="details_cpu")
                dpg.add_text("Memory Usage: ", tag="details_memory")
                dpg.add_text("Last Active: ", tag="details_last_active")

            with dpg.collapsing_header(label="Tasks", default_open=True):
                dpg.add_text("Tasks Completed: ", tag="details_tasks_completed")
                dpg.add_text("Current Task: ", tag="details_current_task")

    def update_agent(self, agent_state):
        """Update single agent state"""
        self.agents[agent_state.name] = agent_state
        self._update_agent_list()
        
        # Update details window if this agent is selected
        if self.selected_agent_id == agent_state.name:
            self._update_agent_details(agent_state)

    def _update_agent_list(self, filtered_agents=None):
        """Update the agent listbox items"""
        if not dpg.does_item_exist("agent_list"):
            return
            
        agents_to_show = filtered_agents or self.agents
        agent_items = [
            f"{agent.name}"  # Simplified display
            for agent in agents_to_show.values()
        ]
        dpg.configure_item("agent_list", items=agent_items)

    def _update_agent_details(self, agent):
        """Update the details window with agent info"""
        if not dpg.does_item_exist("agent_details_window"):
            return
            
        dpg.set_value("details_agent_id", f"Agent ID: {agent.name}")
        dpg.set_value("details_type", f"Type: {agent.agent_type}")
        dpg.set_value("details_role", f"Role: {agent.role}")
        dpg.set_value("details_status", f"Status: {agent.status}")
        dpg.set_value("details_cpu", f"CPU Usage: {agent.cpu_usage:.1f}%")
        dpg.set_value("details_memory", f"Memory Usage: {agent.memory_usage:.1f}MB")
        dpg.set_value("details_last_active", f"Last Active: {agent.last_active}")
        dpg.set_value("details_tasks_completed", f"Tasks Completed: {agent.tasks_completed}")
        dpg.set_value("details_current_task", f"Current Task: {agent.current_task or 'None'}")

    def _filter_agents(self, sender, app_data):
        """Filter agents by type"""
        selected_type = app_data
        if selected_type == "All":
            self._update_agent_list(self.agents)
        else:
            filtered = {
                name: agent for name, agent in self.agents.items()
                if agent.agent_type == selected_type
            }
            self._update_agent_list(filtered)

    def _on_agent_selected(self, sender, app_data):
        """Handle agent selection"""
        self.selected_agent_id = app_data
        
        # Create or update details window
        if not dpg.does_item_exist("agent_details_window"):
            self._create_agent_details_window()
            
        if agent := self.agents.get(self.selected_agent_id):
            self._update_agent_details(agent)