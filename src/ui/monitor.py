# At the top of monitor.py
import dearpygui.dearpygui as dpg
import logging
import queue
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import docker
import tkinter as tk
import math

from src.core.config import SystemConfig
from src.core.workflow import WorkflowManager

# Initialize logger
logger = logging.getLogger(__name__)


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

# src/ui/monitor.py

import dearpygui.dearpygui as dpg
import logging
import queue
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import docker

from src.core.config import SystemConfig
from src.core.workflow import WorkflowManager

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Represents the current state of an agent with enhanced type tracking"""
    name: str
    agent_type: str  # "Research", "Code", "Viz", "QA", "PM"
    role: str
    status: str
    tasks_completed: int
    memory_usage: float
    cpu_usage: float
    last_active: datetime
    position: Tuple[int, int] = (0, 0)
    current_task: Optional[str] = None
    specialization: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

    @property
    def display_name(self) -> str:
        """Returns a formatted display name including the agent type"""
        return f"{self.name} ({self.agent_type})"

class AgentMonitoringSystem:
    """Main monitoring system that handles UI and agent tracking"""
    
    def __init__(self, config: SystemConfig):
        # Add debug logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        
        # Basic state
        self.config = config
        self.message_queue = queue.Queue()
        self.agents: Dict[str, AgentState] = {}
        self.workflows: Dict[str, Dict] = {}
        self.selected_workflow_id: Optional[str] = None
        
        # Performance tracking
        self.agent_performance = defaultdict(list)
        self.metrics = {
            "messages_processed": 0,
            "active_workflows": 0,
            "tasks_completed": 0
        }
        
        # Specialized agent tracking
        self.research_agents = {}
        self.code_agents = {}
        self.viz_agents = {}
        self.qa_agents = {}
        self.pm_agents = {}
        
        self.agent_type_colors = {
            "Research": (0, 150, 255, 255),  # Blue
            "Code": (0, 255, 150, 255),      # Green
            "Viz": (255, 150, 0, 255),       # Orange
            "QA": (255, 0, 150, 255),        # Pink
            "PM": (150, 0, 255, 255)         # Purple
        }
        
        # Initialize components
        self.workflow_manager = WorkflowManager(config, self.message_queue)
        self.docker_client = docker.from_env()
        
        # UI state
        self.width, self.height = get_screen_size_percentage()
        
        logging.info("AgentMonitoringSystem setup.")

    def setup_ui(self):
        """Initialize the monitoring UI"""
        try:
            self.logger.debug("Starting UI setup")
            
            # Setup main window
            with dpg.window(label="Agent Monitor", tag="primary_window", width=-1, height=-1):
                self.logger.debug("Created primary window")
                
                with dpg.group(horizontal=True):
                    # Left panel - Controls and Status (25% of width)
                    left_width = int(self.width * 0.25)
                    with dpg.child_window(width=left_width, height=-1):
                        self._setup_control_panel()
                        self._setup_agent_list()
                    
                    with dpg.child_window(width=-1, height=-1):
                        with dpg.tab_bar():
                            with dpg.tab(label="Workflow View"):
                                self._setup_node_editor()
                            with dpg.tab(label="Metrics"):
                                # self._setup_metrics_view()
                                pass
                            with dpg.tab(label="Message Log"):
                                self._setup_message_log()
                                pass
            
            self.logger.debug("UI setup complete")
            
            # Set as primary window
            dpg.set_primary_window("primary_window", True)
            
        except Exception as e:
            self.logger.error(f"Error in setup_ui: {str(e)}")
            raise

    def _setup_control_panel(self):
        """Setup workflow control panel"""
        with dpg.collapsing_header(label="Workflow Control", default_open=True):
            dpg.add_combo(
                items=["research", "development", "viz"],
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
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Start New Workflow",
                    callback=self.start_new_workflow,
                )
                
                dpg.add_button(
                    label="Stop Selected",
                    callback=self.stop_selected_workflow,
                )

    def run(self):
        """Main application loop"""
        try:
            self.logger.debug("Starting main loop")
            last_performance_update = time.time()
            
            while dpg.is_dearpygui_running():
                try:
                    # Process messages
                    while not self.message_queue.empty():
                        msg = self.message_queue.get_nowait()
                        self.process_message(msg)
                    
                    # Update performances every second
                    current_time = time.time()
                    if current_time - last_performance_update >= 1.0:
                        self.update_agent_performances()
                        last_performance_update = current_time
                    
                    # Update other metrics and UI
                    self.update_metrics()
                    
                except queue.Empty:
                    pass
                except Exception as e:
                    self.logger.error(f"Error in main loop: {str(e)}")
                
                dpg.render_dearpygui_frame()
                
        except Exception as e:
            self.logger.error(f"Error in run method: {str(e)}")
            raise
        
    def update_agent_performances(self):
        """Update performance metrics for all agents"""
        for agent_name, agent in self.agents.items():
            try:
                # Update CPU and memory usage (example values - replace with actual monitoring)
                agent.cpu_usage = psutil.cpu_percent(interval=0.1)
                agent.memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                # Update performance history
                if not hasattr(agent, 'performance_history'):
                    agent.performance_history = [0.0] * 100
                
                # Add new value and maintain fixed length
                agent.performance_history = agent.performance_history[1:] + [agent.cpu_usage]
                
                # Update the node
                self._update_agent_node(agent)
                
            except Exception as e:
                self.logger.error(f"Error updating agent {agent_name} performance: {e}")
    
    def stop_selected_workflow(self, sender, app_data):
        """Stop the currently selected workflow"""
        if self.selected_workflow_id:
            try:
                self.workflow_manager.stop_workflow(self.selected_workflow_id)
                logger.info(f"Stopped workflow {self.selected_workflow_id}")
            except Exception as e:
                logger.error(f"Error stopping workflow: {e}")
    
    def _setup_status_panel(self):
        """Setup system status panel"""
        with dpg.collapsing_header(label="System Status", default_open=True):
            dpg.add_text("Active Agents: 0", tag="active_agents_text")
            dpg.add_text("Active Workflows: 0", tag="active_workflows_text")
            dpg.add_text("Messages: 0", tag="messages_text")
            dpg.add_text("Uptime: 00:00:00", tag="uptime_text")

    def _setup_visualization_tabs(self):
        """Setup visualization tabs"""
        with dpg.tab_bar():
            # Workflow Graph Tab
            with dpg.tab(label="Workflow Graph"):
                self.graph_view = dpg.add_drawlist(
                    width=-1, 
                    height=int(self.height * 0.7)
                )
            
            # Message Log Tab
            with dpg.tab(label="Message Log"):
                self.message_log = dpg.add_child_window(
                    width=-1,
                    height=int(self.height * 0.7)
                )
                # Add a clear button for the log
                dpg.add_button(
                    label="Clear Log",
                    callback=lambda: dpg.delete_item(self.message_log, children_only=True),
                    parent=self.message_log
                )
            
            # Metrics Tab
            with dpg.tab(label="Metrics"):
                self._setup_metrics_plot()

    def view_agent_details(self, sender, app_data):
        """Show detailed information about selected agent"""
        agent_name = dpg.get_value("agent_list")
        if not agent_name:
            return
            
        agent = self.agents.get(agent_name)
        if not agent:
            return
        
        # Create or configure the details window
        if not dpg.does_item_exist("agent_details_window"):
            with dpg.window(
                label="Agent Details",
                tag="agent_details_window",
                pos=(int(self.width * 0.3), int(self.height * 0.3)),
                width=400,
                height=300,
                show=True
            ):
                dpg.add_text("", tag="agent_details_text")
        
        # Update details text
        details = f"""Name: {agent.get('name', 'N/A')}
        Status: {agent.get('status', 'N/A')}
        Role: {agent.get('role', 'N/A')}
        Tasks Completed: {len(agent.get('tasks', []))}
        Current Task: {agent.get('current_task', 'None')}"""
            
        dpg.configure_item("agent_details_text", default_value=details)
        dpg.show_item("agent_details_window")

    def select_agent(self, sender, app_data):
        """Handle agent selection from the list"""
        selected_agent = self.agents.get(app_data)
        if selected_agent:
            logger.info(f"Selected agent: {app_data}")
            # Update UI elements for selected agent

    def update_metrics(self):
        """Update UI metrics - safe to call from render loop"""
        if dpg.does_alias_exist("active_agents_text"):
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
                
    def _setup_node_editor(self):
        """Setup the node editor for agent visualization"""
        with dpg.node_editor(
            callback=self._on_node_connect,
            delink_callback=self._on_node_disconnect,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            tag="agent_node_editor"
        ):
            # Node editor will be populated dynamically
            pass
            
        # Add a tooltip to explain controls
        # with dpg.tooltip(parent="agent_node_editor"):
        #     dpg.add_text("Ctrl+Click to remove connections\nDrag nodes to reposition")


    def _add_agent_node(self, agent: AgentState):
        """Add a new agent node to the editor with proper styling and attributes"""
        
        # Generate unique node ID
        node_id = f"node_{agent.name}"
        
        # Calculate initial position if not set
        if agent.position == (0, 0):
            num_nodes = len(self.agents)
            x = 100 + (num_nodes % 3) * 250  # 3 columns
            y = 100 + (num_nodes // 3) * 200  # 200px vertical spacing
            agent.position = (x, y)

        # Create node theme with agent-type specific colors
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvNode):
                color = self.agent_type_colors.get(agent.agent_type, (150, 150, 150, 255))
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, color, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, color, category=dpg.mvThemeCat_Nodes)

        # Create the node
        with dpg.node(
            label=f"{agent.agent_type} Agent: {agent.name}",
            tag=node_id,
            parent="agent_node_editor",
            pos=agent.position
        ):
            # Bind the theme
            dpg.bind_item_theme(node_id, node_theme)
            
            # Input attribute for receiving connections
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag=f"input_{agent.name}"):
                dpg.add_text("Input")
                
            # Static attributes for agent info
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                # Status indicator with color
                status_colors = {
                    "active": [0, 255, 0, 255],    # Green
                    "idle": [150, 150, 150, 255],  # Gray
                    "busy": [255, 165, 0, 255],    # Orange
                    "error": [255, 0, 0, 255]      # Red
                }
                with dpg.group(horizontal=True):
                    dpg.add_text("Status: ")
                    dpg.add_text(
                        agent.status,
                        tag=f"status_text_{agent.name}",
                        color=status_colors.get(agent.status.lower(), [255, 255, 255, 255])
                    )

                # Add current task
                dpg.add_text("Current Task:", tag=f"task_label_{agent.name}")
                dpg.add_text(
                    agent.current_task or "None",
                    tag=f"task_text_{agent.name}",
                    wrap=300
                )

                # Add performance metrics
                with dpg.group(horizontal=True):
                    dpg.add_text("CPU: ")
                    dpg.add_text(
                        f"{agent.cpu_usage:.1f}%",
                        tag=f"cpu_text_{agent.name}"
                    )
                
                with dpg.group(horizontal=True):
                    dpg.add_text("Memory: ")
                    dpg.add_text(
                        f"{agent.memory_usage:.1f}MB",
                        tag=f"memory_text_{agent.name}"
                    )

                # Add mini performance plot
                dpg.add_simple_plot(
                    label="Performance",
                    default_value=(0.0,) * 100,  # Initialize with zeros
                    width=200,
                    height=50,
                    tag=f"performance_plot_{agent.name}"
                )

            # Output attribute for making connections
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=f"output_{agent.name}"):
                dpg.add_text("Output")

            # Add right-click context menu
            with dpg.popup(parent=node_id, mousebutton=dpg.mvMouseButton_Right):
                dpg.add_menu_item(label="View Details", callback=lambda: self._view_agent_details(agent.name))
                dpg.add_menu_item(label="Reset Position", callback=lambda: self._reset_node_position(agent.name))
                dpg.add_menu_item(label="Focus Agent", callback=lambda: self._focus_on_node(agent.name))
    
    def _focus_on_node(self, agent_name: str):
        """Center the node editor view on a specific agent node"""
        node_id = f"node_{agent_name}"
        if dpg.does_item_exist(node_id):
            pos = dpg.get_item_pos(node_id)
            editor_pos = dpg.get_item_pos("agent_node_editor")
            editor_size = dpg.get_item_rect_size("agent_node_editor")
            
            # Calculate center position
            center_x = editor_pos[0] + editor_size[0]/2 - pos[0]
            center_y = editor_pos[1] + editor_size[1]/2 - pos[1]
            
            # Smoothly pan to the node
            dpg.set_node_editor_panning(center_x, center_y)

    
    def _update_agent_node(self, agent: AgentState):
        """Update an existing agent node's information with enhanced error logging"""
        try:
            # Get all relevant item tags before updating
            status_tag = f"status_text_{agent.name}"
            task_tag = f"task_text_{agent.name}"
            cpu_tag = f"cpu_text_{agent.name}"
            memory_tag = f"memory_text_{agent.name}"
            plot_tag = f"performance_plot_{agent.name}"

            # Log the items we're trying to update
            self.logger.debug(f"Updating node items for agent {agent.name}: "
                            f"status={status_tag}, task={task_tag}, "
                            f"cpu={cpu_tag}, memory={memory_tag}, plot={plot_tag}")

            # Check if items exist before updating
            for tag in [status_tag, task_tag, cpu_tag, memory_tag, plot_tag]:
                if not dpg.does_item_exist(tag):
                    self.logger.error(f"Item {tag} does not exist!")
                    continue

                try:
                    # Status update
                    if tag == status_tag:
                        status_colors = {
                            "active": [0, 255, 0, 255],
                            "idle": [150, 150, 150, 255],
                            "busy": [255, 165, 0, 255],
                            "error": [255, 0, 0, 255]
                        }
                        dpg.configure_item(
                            tag,
                            default_value=agent.status,
                            color=status_colors.get(agent.status.lower(), [255, 255, 255, 255])
                        )
                        self.logger.debug(f"Updated status for {agent.name}: {agent.status}")

                    # Task update
                    elif tag == task_tag:
                        dpg.configure_item(
                            tag,
                            default_value=agent.current_task or "None"
                        )
                        self.logger.debug(f"Updated task for {agent.name}: {agent.current_task}")

                    # CPU update
                    elif tag == cpu_tag:
                        dpg.configure_item(
                            tag,
                            default_value=f"{agent.cpu_usage:.1f}%"
                        )
                        self.logger.debug(f"Updated CPU for {agent.name}: {agent.cpu_usage:.1f}%")

                    # Memory update
                    elif tag == memory_tag:
                        dpg.configure_item(
                            tag,
                            default_value=f"{agent.memory_usage:.1f}MB"
                        )
                        self.logger.debug(f"Updated memory for {agent.name}: {agent.memory_usage:.1f}MB")

                    # Performance plot update
                    elif tag == plot_tag and hasattr(agent, 'performance_history'):
                        dpg.configure_item(
                            tag,
                            default_value=agent.performance_history
                        )
                        self.logger.debug(f"Updated performance plot for {agent.name}")

                except Exception as item_error:
                    # Get DPG's last error
                    dpg_error = dpg.get_text_error()
                    self.logger.error(f"Error updating {tag} for agent {agent.name}:")
                    self.logger.error(f"Exception: {str(item_error)}")
                    self.logger.error(f"DPG Error: {dpg_error}")
                    if hasattr(item_error, '__traceback__'):
                        import traceback
                        self.logger.error("Traceback:")
                        self.logger.error(traceback.format_tb(item_error.__traceback__))

        except Exception as e:
            # Get DPG's last error
            dpg_error = dpg.get_text_error()
            self.logger.error(f"Critical error updating agent node {agent.name}:")
            self.logger.error(f"Exception: {str(e)}")
            self.logger.error(f"DPG Error: {dpg_error}")
            if hasattr(e, '__traceback__'):
                import traceback
                self.logger.error("Traceback:")
                self.logger.error(traceback.format_tb(e.__traceback__))

    def setup_logging(self):
        """Setup enhanced logging configuration"""
        # Create a formatter that includes more details
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Create console handler with formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Create file handler with formatter
        file_handler = logging.FileHandler('agent_monitor.log')
        file_handler.setFormatter(formatter)
        
        # Get logger and add handlers
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
        
        # Also log DPG version and initialization
        self.logger.info(f"DearPyGui Version: {dpg.get_dearpygui_version()}")
        self.logger.info("Initializing Agent Monitoring System")

    def _get_role_color(self, role: str) -> tuple:
        """Get color theme for different agent roles"""
        colors = {
            "research": (0, 150, 255, 255),   # Blue
            "code": (0, 255, 150, 255),       # Green
            "viz": (255, 150, 0, 255),        # Orange
            "qa": (255, 0, 150, 255),         # Pink
            "pm": (150, 0, 255, 255)          # Purple
        }
        return colors.get(role.lower(), (150, 150, 150, 255))

    def _on_node_connect(self, sender, app_data):
        """Handle connection between agent nodes"""
        try:
            # Extract source and target node IDs
            source_attr_id, target_attr_id = app_data
            source_agent = source_attr_id.split('_')[1]
            target_agent = target_attr_id.split('_')[1]

            # Create the link
            link_id = dpg.add_node_link(source_attr_id, target_attr_id, parent=sender)

            # Log the connection
            self.log_message(
                f"Connected {self.agents[source_agent].agent_type} agent '{source_agent}' to "
                f"{self.agents[target_agent].agent_type} agent '{target_agent}'",
                "info"
            )

            # Update workflow connections
            if self.selected_workflow_id:
                self._add_workflow_connection(source_agent, target_agent)

        except Exception as e:
            self.logger.error(f"Error creating node connection: {e}")
            
    
    def _reset_node_position(self, agent_name: str):
        """Reset an agent node to its default position"""
        node_id = f"node_{agent_name}"
        if dpg.does_item_exist(node_id):
            num_nodes = len(self.agents)
            x = 100 + (num_nodes % 3) * 250
            y = 100 + (num_nodes // 3) * 200
            dpg.set_item_pos(node_id, [x, y])

    def _add_workflow_connection(self, source_agent: str, target_agent: str):
        """Add a connection to the current workflow"""
        if self.selected_workflow_id and self.selected_workflow_id in self.workflows:
            workflow = self.workflows[self.selected_workflow_id]
            workflow['connections'].append({
                'from': source_agent,
                'to': target_agent,
                'timestamp': datetime.now().isoformat()
            })

    def _on_node_disconnect(self, sender, app_data):
        """Handle disconnection between agent nodes"""
        try:
            # Extract node IDs from attribute IDs
            from_node = app_data[0].split('_')[1]
            to_node = app_data[1].split('_')[1]
            
            # Log the disconnection
            self.log_message({
                'type': 'System',
                'content': f'Connection removed between {from_node} and {to_node}'
            })
            
            # Update workflow connections
            if self.selected_workflow_id:
                workflow = self.workflows.get(self.selected_workflow_id)
                if workflow:
                    workflow['connections'] = [
                        conn for conn in workflow['connections']
                        if not (conn['from'] == from_node and conn['to'] == to_node)
                    ]
                    self._update_workflow(self.selected_workflow_id, workflow)
            
        except Exception as e:
            logger.error(f"Error handling node disconnection: {e}")

    def _auto_layout_nodes(self):
        """Automatically arrange nodes in a force-directed layout"""
        try:
            if not self.selected_workflow_id:
                return
                
            workflow = self.workflows.get(self.selected_workflow_id)
            if not workflow:
                return
            
            # Create networkx graph from connections
            G = nx.Graph()
            
            # Add nodes
            for agent in workflow['agents']:
                G.add_node(agent['id'])
            
            # Add edges
            for conn in workflow['connections']:
                G.add_edge(conn['from'], conn['to'])
            
            # Calculate layout
            pos = nx.spring_layout(G)
            
            # Scale and translate positions to fit in the node editor
            editor_width = dpg.get_item_width("agent_node_editor")
            editor_height = dpg.get_item_height("agent_node_editor")
            margin = 50
            
            for node_id, position in pos.items():
                x = (position[0] + 1) * (editor_width - 2*margin)/2 + margin
                y = (position[1] + 1) * (editor_height - 2*margin)/2 + margin
                dpg.set_item_pos(f"node_{node_id}", [x, y])
            
        except Exception as e:
            logger.error(f"Error in auto-layout: {e}")

    def _add_node_context_menu(self):
        """Add context menu for nodes"""
        with dpg.handler_registry():
            dpg.add_item_clicked_handler(callback=self._show_node_context_menu, button=dpg.mvMouseButton_Right)

    def _show_node_context_menu(self, sender, app_data, user_data):
        """Show context menu for node interactions"""
        if dpg.does_item_exist("node_context_menu"):
            dpg.delete_item("node_context_menu")
        
        # Get clicked node
        clicked_node = dpg.get_item_info(sender)["parent"]
        if not clicked_node.startswith("node_"):
            return
            
        node_id = clicked_node.split("_")[1]
        
        # Create context menu
        with dpg.window(label="Node Menu", tag="node_context_menu", popup=True):
            dpg.add_text(f"Node: {node_id}")
            dpg.add_separator()
            
            # Add menu items
            dpg.add_menu_item(
                label="View Details",
                callback=lambda: self.view_agent_details(node_id)
            )
            dpg.add_menu_item(
                label="Reset Position",
                callback=lambda: dpg.reset_pos(clicked_node)
            )
            dpg.add_menu_item(
                label="Remove Node",
                callback=lambda: self._remove_agent_node(node_id)
            )

    def _remove_agent_node(self, agent_id: str):
        """Remove an agent node from the editor"""
        try:
            # Remove from workflow
            if self.selected_workflow_id:
                workflow = self.workflows.get(self.selected_workflow_id)
                if workflow:
                    workflow['agents'] = [
                        agent for agent in workflow['agents']
                        if agent['id'] != agent_id
                    ]
                    workflow['connections'] = [
                        conn for conn in workflow['connections']
                        if conn['from'] != agent_id and conn['to'] != agent_id
                    ]
                    self._update_workflow(self.selected_workflow_id, workflow)
            
            # Remove node from editor
            dpg.delete_item(f"node_{agent_id}")
            
            self.log_message({
                'type': 'System',
                'content': f'Removed agent {agent_id} from workflow'
            })
            
        except Exception as e:
            logger.error(f"Error removing agent node: {e}")
            

    def _setup_message_log(self):
        """Setup the message log panel"""
        with dpg.child_window(label="Message Log", height=-1):
            # Add message filter controls
            with dpg.group(horizontal=True):
                dpg.add_combo(
                    label="Filter",
                    items=["All", "Info", "Warning", "Error"],
                    default_value="All",
                    callback=self._filter_messages,
                    tag="message_filter"
                )
                dpg.add_button(label="Clear", callback=self._clear_messages)
            
            # Message log container
            dpg.add_child_window(tag="message_list", height=-1)

    def _setup_agent_list(self):
        """Enhanced agent list setup with type information"""
        with dpg.collapsing_header(label="Agent List", default_open=True):
            # Add agent type filter
            dpg.add_combo(
                label="Filter by Type",
                items=["All", "Research", "Code", "Viz", "QA", "PM"],
                default_value="All",
                callback=self._filter_agents,
                tag="agent_type_filter"
            )
            
            # Enhanced listbox with agent types
            dpg.add_listbox(
                tag="agent_list",
                items=[],
                num_items=10,
                callback=self._on_agent_selected,
                width=-1
            )

    def _on_agent_selected(self, sender, app_data):
        """Handle agent selection from list"""
        self.selected_agent_id = app_data
        self._view_agent_details()
        self.logger.debug(f"Selected agent: {app_data}")

    def _get_agent_type_for_workflow(self, workflow_type: str) -> str:
        """Determine appropriate agent type based on workflow type"""
        type_mapping = {
            "research": "Research",
            "development": "Code",
            "viz": "Viz",
            "qa": "QA",
            "management": "PM"
        }
        return type_mapping.get(workflow_type.lower(), "Code")

    def _view_agent_details(self):
        """Enhanced agent details view"""
        if not hasattr(self, 'selected_agent_id'):
            return
            
        agent = self.agents.get(self.selected_agent_id)
        if not agent:
            return
        
        # Create or update details window with enhanced information
        if not dpg.does_item_exist("agent_details_window"):
            with dpg.window(
                label="Agent Details",
                tag="agent_details_window",
                pos=(int(self.width * 0.3), int(self.height * 0.3)),
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

    def start_new_workflow(self, sender, app_data):
        """Enhanced workflow creation with proper agent type assignment"""
        try:
            workflow_type = dpg.get_value("workflow_type")
            task = dpg.get_value("task_input")
            
            if not task.strip():
                self.log_message("Task description required", "error")
                return
            
            # Create workflow
            workflow_id = self.workflow_manager.create_workflow(
                workflow_type=workflow_type,
                task=task
            )
            
            # Determine appropriate agent type based on workflow
            agent_type = self._get_agent_type_for_workflow(workflow_type)
            
            # Create agent with proper type
            agent = AgentState(
                name=f"agent_{len(self.agents)}",
                agent_type=agent_type,
                role=workflow_type,
                status="active",
                tasks_completed=0,
                memory_usage=0.0,
                cpu_usage=0.0,
                last_active=datetime.now(),
                current_task=task
            )
            self.agents[agent.name] = agent
            
            # **Add this line to create the agent node in the UI**
            self._add_agent_node(agent)
            
            # Update UI
            self._update_agent_list()
            self.log_message(f"Started new {workflow_type} workflow with {agent_type} agent: {workflow_id}", "info")
            
        except Exception as e:
            self.logger.error(f"Error starting workflow: {e}")
            self.log_message(f"Error starting workflow: {str(e)}", "error")



    def _update_agent_list(self):
        """Update the agent list with type information"""
        if dpg.does_item_exist("agent_list"):
            # Format agent names to include their types
            agent_items = [
                agent.display_name
                for agent in self.agents.values()
            ]
            dpg.configure_item("agent_list", items=agent_items)

    def log_message(self, message: str, level: str = "info"):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with dpg.mutex():
            if dpg.does_item_exist("message_list"):
                dpg.add_text(
                    f"[{timestamp}] {level.upper()}: {message}",
                    parent="message_list",
                    color=self._get_message_color(level)
                )

    def _get_message_color(self, level: str) -> tuple:
        """Get color for different message types"""
        colors = {
            "info": (255, 255, 255),    # White
            "success": (0, 255, 0),     # Green
            "warning": (255, 255, 0),   # Yellow
            "error": (255, 0, 0)        # Red
        }
        return colors.get(level, (255, 255, 255))

    def _clear_messages(self):
        """Clear all messages from the log"""
        if dpg.does_item_exist("message_list"):
            dpg.delete_item("message_list", children_only=True)

    def _filter_messages(self, sender, app_data):
        """Filter messages based on level"""
        # To be implemented when we add message storage
        pass