import logging
import queue
import threading
import time
import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional
import networkx as nx
import math
from datetime import datetime
import tkinter as tk

from src.config import SystemConfig
from src.workflow_manager import WorkflowManager

def get_screen_size_percentage(percentage=0.80):
    # Create a root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Get the screen width and height
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the width and height based on the percentage
    width = int(screen_width * percentage)
    height = int(screen_height * percentage)

    # Destroy the root window
    root.destroy()

    return width, height

logger = logging.getLogger(__name__)

class AgentMonitor:
    def __init__(self, config: SystemConfig):
        self.message_queue = queue.Queue()
        self.agents: Dict[str, Dict] = {}
        self.workflows: Dict[str, Dict] = {}  # Single workflow store
        self.selected_workflow_id: Optional[str] = None
        
        # View IDs
        self.graph_view: Optional[int] = None
        self.timeline_view: Optional[int] = None
        self.message_log: Optional[int] = None
        
        # Performance metrics
        self.metrics = {
            "messages_processed": 0,
            "active_workflows": 0,
            "tasks_completed": 0
        }
        
        self.width, self.height = get_screen_size_percentage()
        
        # Create context
        dpg.create_context()
        
        self.workflow_manager = WorkflowManager(config, self.message_queue)
    
    def _setup_control_panel(self):
        """Setup workflow control panel"""
        with dpg.collapsing_header(label="Workflow Control", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_combo(
                    ["research", "development"],
                    label="Workflow Type",
                    default_value="research",
                    tag="workflow_type"
                )
            
            dpg.add_input_text(
                label="Task Description",
                multiline=True,
                height=100,
                tag="task_input"
            )
            
            dpg.add_button(
                label="Start New Workflow",
                callback=self.start_new_workflow,
                width=-1
            )
            dpg.add_button(
                label="Stop Selected Workflow",
                callback=self.stop_selected_workflow,
                width=-1
            )
    
    def start_new_workflow(self, sender, app_data):
        """Start a new agent workflow"""
        try:
            workflow_type = dpg.get_value("workflow_type")
            task = dpg.get_value("task_input")
            
            if not task.strip():
                logger.warning("Task description required")
                return
            
            # Create and start workflow
            workflow_id = self.workflow_manager.create_workflow(
                workflow_type=workflow_type,
                task=task
            )
            self.workflow_manager.start_workflow(workflow_id)
            
            # Clear input
            dpg.set_value("task_input", "")
            
            logger.info(f"Started new {workflow_type} workflow: {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
    
    def stop_selected_workflow(self, sender, app_data):
        """Stop the currently selected workflow"""
        if self.selected_workflow_id:
            try:
                self.workflow_manager.stop_workflow(self.selected_workflow_id)
                logger.info(f"Stopped workflow {self.selected_workflow_id}")
            except Exception as e:
                logger.error(f"Error stopping workflow: {e}")

    def setup_ui(self):
        """Initialize the monitoring UI components"""
        # Create viewport
        dpg.create_viewport(title="Agent Monitoring System", width=self.width, height=self.height)
        
        with dpg.window(label="Agent Monitor", tag="primary_window"):
            with dpg.group(horizontal=True):
                # Left panel - Controls and Status
                with dpg.child_window(width=300, height=800):
                    with dpg.collapsing_header(label="System Status", default_open=True):
                        dpg.add_text("Active Agents:", tag="active_agents_text")
                        dpg.add_text("Active Workflows:", tag="active_workflows_text")
                        dpg.add_text("Messages Processed:", tag="messages_text")
                    
                    with dpg.collapsing_header(label="Workflow Control", default_open=True):
                        dpg.add_button(label="Start New Workflow", callback=self.start_new_workflow)
                        dpg.add_button(label="Stop Selected", callback=self.stop_selected_workflow)
                        
                    with dpg.collapsing_header(label="Agent List", default_open=True):
                        self.agent_list = dpg.add_listbox(
                            tag="agent_list",
                            items=[],
                            num_items=10,
                            callback=self.select_agent
                        )

                # Right panel - Visualizations
                with dpg.child_window(width=900, height=800):
                    with dpg.tab_bar():
                        with dpg.tab(label="Workflow Graph"):
                            self.graph_view = dpg.add_drawlist(width=880, height=400)
                            
                        with dpg.tab(label="Message Log"):
                            self.message_log = dpg.add_child_window(width=880, height=400)
                            
                        with dpg.tab(label="Metrics"):
                            with dpg.plot(label="Activity Over Time", height=400):
                                dpg.add_plot_legend()
                                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                                self.x_axis = dpg.last_item()
                                dpg.add_plot_axis(dpg.mvYAxis, label="Count")
                                self.y_axis = dpg.last_item()
                                
                                self.message_series = dpg.add_line_series(
                                    [], [], label="Messages",
                                    parent=self.y_axis
                                )

        # Set primary window and show viewport
        dpg.set_primary_window("primary_window", True)

    def start_new_workflow(self, sender, app_data):
        """Start a new agent workflow"""
        logger.info("Starting new workflow")
        # Implementation here - safe to call from UI thread

    def stop_selected_workflow(self, sender, app_data):
        """Stop the currently selected workflow"""
        if self.selected_workflow_id:
            logger.info(f"Stopping workflow {self.selected_workflow_id}")
            # Implementation here - safe to call from UI thread

    def select_agent(self, sender, app_data):
        """Handle agent selection from the list"""
        selected_agent = self.agents.get(app_data)
        if selected_agent:
            logger.info(f"Selected agent: {app_data}")
            # Update UI elements for selected agent

    def update_metrics(self):
        """Update UI metrics - safe to call from render loop"""
        dpg.set_value("active_agents_text", f"Active Agents: {len(self.agents)}")
        dpg.set_value("active_workflows_text", f"Active Workflows: {self.metrics['active_workflows']}")
        dpg.set_value("messages_text", f"Messages: {self.metrics['messages_processed']}")

    def update_graph(self):
        """Update the workflow graph visualization - safe to call from render loop"""
        if not self.selected_workflow_id:
            return

        workflow = self.workflows.get(self.selected_workflow_id)
        if not workflow:
            return

        # Clear previous graph
        dpg.delete_item(self.graph_view, children_only=True)
        
        # Draw nodes and edges
        node_positions = {}
        for agent in workflow['agents']:
            x = len(node_positions) * 100 + 50
            y = 200
            node_positions[agent['name']] = (x, y)
            
            # Draw node
            dpg.draw_circle((x, y), 20, parent=self.graph_view, fill=(0, 255, 0, 100))
            dpg.draw_text((x-30, y+25), agent['name'], parent=self.graph_view)

        # Draw edges for interactions
        for interaction in workflow['interactions']:
            if interaction['from'] in node_positions and interaction['to'] in node_positions:
                start = node_positions[interaction['from']]
                end = node_positions[interaction['to']]
                dpg.draw_line(start, end, parent=self.graph_view, color=(255, 255, 255, 100))

    def process_message(self, message: Dict):
        """Process incoming messages - safe to call from render loop"""
        msg_type = message.get('type')
        
        if msg_type == 'new_agent':
            self.agents[message['agent_id']] = message['data']
            
        elif msg_type == 'agent_update':
            if message['agent_id'] in self.agents:
                self.agents[message['agent_id']].update(message['data'])
                
        elif msg_type == 'new_workflow':
            self.workflows[message['workflow_id']] = message['data']
            self.metrics['active_workflows'] += 1
            
        elif msg_type == 'workflow_update':
            if message['workflow_id'] in self.workflows:
                self.workflows[message['workflow_id']].update(message['data'])
                
        elif msg_type == 'message':
            self.metrics['messages_processed'] += 1

        # Update UI elements
        dpg.configure_item("agent_list", items=list(self.agents.keys()))
        
    def select_workflow_callback(self, sender, app_data, user_data):
        """Callback for when a workflow is selected in the UI"""
        self.selected_workflow_id = user_data
        self.update_views()

    def update_views(self):
        """Update both graph and timeline views based on selected workflow"""
        if self.selected_workflow_id and self.selected_workflow_id in self.active_workflows:
            workflow = self.active_workflows[self.selected_workflow_id]
            self.update_graph_view(workflow)
            self.update_timeline_view(workflow)

    def update_graph_view(self, workflow: Dict):
        """Update the graph visualization of agent interactions"""
        if not self.graph_view_id:
            return

        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes for each agent
        for agent in workflow['agents']:
            G.add_node(agent['name'], role=agent['role'])

        # Add edges for interactions
        for interaction in workflow['interactions']:
            G.add_edge(
                interaction['from'],
                interaction['to'],
                timestamp=interaction['timestamp']
            )

        # Clear previous graph
        dpg.delete_item(self.graph_view_id, children_only=True)

        # Create layout
        pos = nx.spring_layout(G)
        
        # Draw nodes
        for node in G.nodes():
            x, y = pos[node]
            dpg.draw_circle(
                center=[x * 100 + 200, y * 100 + 200],
                radius=20,
                fill=[0, 255, 0, 255],
                parent=self.graph_view_id
            )
            dpg.draw_text(
                pos=[x * 100 + 180, y * 100 + 190],
                text=node,
                parent=self.graph_view_id
            )

        # Draw edges
        for edge in G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            dpg.draw_line(
                p1=[start_pos[0] * 100 + 200, start_pos[1] * 100 + 200],
                p2=[end_pos[0] * 100 + 200, end_pos[1] * 100 + 200],
                color=[255, 255, 255, 255],
                parent=self.graph_view_id
            )

    def update_timeline_view(self, workflow: Dict):
        """Update the timeline visualization of agent activities"""
        if not self.timeline_view_id:
            return

        # Clear previous timeline
        dpg.delete_item(self.timeline_view_id, children_only=True)

        # Sort interactions by timestamp
        interactions = sorted(
            workflow['interactions'],
            key=lambda x: datetime.fromisoformat(x['timestamp'])
        )

        # Calculate timeline dimensions
        timeline_start = datetime.fromisoformat(interactions[0]['timestamp'])
        timeline_end = datetime.fromisoformat(interactions[-1]['timestamp'])
        total_duration = (timeline_end - timeline_start).total_seconds()

        # Draw timeline base
        dpg.draw_line(
            p1=[50, 250],
            p2=[550, 250],
            color=[255, 255, 255, 255],
            parent=self.timeline_view_id
        )

        # Draw interactions on timeline
        for idx, interaction in enumerate(interactions):
            timestamp = datetime.fromisoformat(interaction['timestamp'])
            position = (timestamp - timeline_start).total_seconds() / total_duration
            x_pos = 50 + position * 500

            # Draw marker
            dpg.draw_circle(
                center=[x_pos, 250],
                radius=5,
                fill=[0, 255, 0, 255],
                parent=self.timeline_view_id
            )

            # Draw label
            dpg.draw_text(
                pos=[x_pos - 20, 260],
                text=f"{interaction['from']} → {interaction['to']}",
                parent=self.timeline_view_id
            )

    def register_workflow(self, workflow_id: str, workflow_data: Dict):
        """Register a new workflow to be monitored"""
        self.active_workflows[workflow_id] = workflow_data
        if not self.selected_workflow_id:
            self.selected_workflow_id = workflow_id
            self.update_views()

    def update_workflow(self, workflow_id: str, workflow_data: Dict):
        """Update an existing workflow's data"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id] = workflow_data
            if workflow_id == self.selected_workflow_id:
                self.update_views()

    def run(self):
        """Main application loop using DearPyGui's render loop"""
        # Setup and show viewport
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Main loop
        while dpg.is_dearpygui_running():
            # Process any messages in queue
            try:
                while not self.message_queue.empty():
                    msg = self.message_queue.get_nowait()
                    self.process_message(msg)
            except queue.Empty:
                pass

            # Update UI
            self.update_metrics()
            self.update_graph()
            
            # Render frame
            dpg.render_dearpygui_frame()

        # Cleanup
        dpg.destroy_context()

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Create and run monitor
        monitor = AgentMonitor()
        monitor.setup_ui()
        # Create test data
        monitor.message_queue.put({
            "type": "new_agent",
            "agent_id": "researcher_1",
            "data": {
                "name": "Researcher",
                "status": "active",
                "tasks": []
            }
        })

        # Run the monitor
        monitor.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise