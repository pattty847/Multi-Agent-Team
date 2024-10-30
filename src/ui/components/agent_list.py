# components/agent_list.py
from typing import Dict
import dearpygui.dearpygui as dpg

from src.ui.state.agent import AgentState

class AgentListView:
    def __init__(self, parent_id: int):
        self.parent_id = parent_id
        self.selected_agent_id = None

    def setup(self):
        with dpg.collapsing_header(label="Agent List", default_open=True, parent=self.parent_id):
            dpg.add_combo(
                label="Filter by Type",
                items=["All", "Research", "Code", "Viz", "QA", "PM"],
                default_value="All",
                callback=self._filter_agents,
                tag="agent_type_filter"
            )
            
            dpg.add_listbox(
                tag="agent_list",
                items=[],
                num_items=10,
                callback=self._on_agent_selected,
                width=-1
            )

    def update_agents(self, agents: Dict[str, AgentState]):
        # Format agent names to include their types
        agent_items = [
            f"{agent.name} ({agent.agent_type})"
            for agent in agents.values()
        ]
        dpg.configure_item("agent_list", items=agent_items)
        
    def _filter_agents(self, sender, app_data):
        """Filter agents by type"""
        selected_type = app_data
        if selected_type == "All":
            self._update_agent_list()
        else:
            filtered_agents = {
                name: agent for name, agent in self.agents.items()
                if agent.agent_type == selected_type
            }
            agent_items = [agent.display_name for agent in filtered_agents.values()]
            dpg.configure_item("agent_list", items=agent_items)

    def _on_agent_selected(self, sender, app_data):
        """Handle agent selection from list"""
        self.selected_agent_id = app_data
        self._view_agent_details()
        
    def _view_agent_details(self):
        """Show detailed agent information window"""
        if not self.selected_agent_id:
            return
            
        agent = self.agents.get(self.selected_agent_id)
        if not agent:
            return
        
        # Create or update details window
        if not self.details_window_created:
            with dpg.window(
                label="Agent Details",
                tag="agent_details_window",
                pos=(int(dpg.get_viewport_width() * 0.3), 
                     int(dpg.get_viewport_height() * 0.3)),
                width=400,
                height=300,
                show=True
            ):
                # Add collapsing headers for organized information
                with dpg.collapsing_header(label="Basic Info", default_open=True):
                    dpg.add_text("", tag="agent_basic_info")
                    
                with dpg.collapsing_header(label="Performance", default_open=True):
                    dpg.add_text("", tag="agent_performance")
                    
                with dpg.collapsing_header(label="Tasks", default_open=True):
                    dpg.add_text("", tag="agent_tasks")
            
            self.details_window_created = True

        # Update information sections
        basic_info = (
            f"Agent ID: {agent.name}\n"
            f"Type: {agent.agent_type}\n"
            f"Role: {agent.role}\n"
            f"Status: {agent.status}"
        )
        dpg.set_value("agent_basic_info", basic_info)
        
        performance_info = (
            f"CPU Usage: {agent.cpu_usage:.1f}%\n"
            f"Memory Usage: {agent.memory_usage:.1f}MB\n"
            f"Last Active: {agent.last_active.strftime('%H:%M:%S')}"
        )
        dpg.set_value("agent_performance", performance_info)
        
        tasks_info = (
            f"Tasks Completed: {agent.tasks_completed}\n"
            f"Current Task: {agent.current_task or 'None'}"
        )
        dpg.set_value("agent_tasks", tasks_info)
        
        dpg.show_item("agent_details_window")

    def update_agents(self, agents: Dict):
        """Update the agent list with new agent data"""
        self.agents = agents  # Store reference to agents
        self._update_agent_list()

    def _update_agent_list(self):
        """Update the agent list UI"""
        if dpg.does_item_exist("agent_list"):
            agent_items = [
                agent.display_name
                for agent in self.agents.values()
            ]
            dpg.configure_item("agent_list", items=agent_items)