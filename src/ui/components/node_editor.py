# components/node_editor.py
import dearpygui.dearpygui as dpg
from typing import Dict, Optional, Tuple

from src.ui.state.app_state import AppState

class NodeEditorView:
    def __init__(self, parent_id: int, app_state: AppState):
        self.parent_id = parent_id
        self.app_state = app_state
        self.nodes: Dict[str, int] = {}  # Maps agent_id to node_id
        self.selected_node_id: Optional[str] = None
        self.agent_type_colors = {
            "Research": [0, 150, 255, 255],  # Blue
            "Code": [0, 255, 150, 255],      # Green
            "Viz": [255, 150, 0, 255],       # Orange
            "QA": [255, 0, 150, 255],        # Pink
            "PM": [150, 0, 255, 255]         # Purple
        }

    def setup(self):
        """Initialize the node editor"""
        with dpg.node_editor(
            callback=self._on_node_connect,
            delink_callback=self._on_node_disconnect,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            tag="agent_node_editor"
        ):
            pass  # Nodes will be added dynamically

    def _add_agent_node(self, agent_state) -> int:
        """Add a new agent node to the editor"""
        # Generate unique node ID
        node_id = f"node_{agent_state.name}"
        
        # Calculate initial position if not set
        if agent_state.position == (0, 0):
            num_nodes = len(self.nodes)
            x = 100 + (num_nodes % 3) * 250  # 3 columns
            y = 100 + (num_nodes // 3) * 200  # 200px vertical spacing
            agent_state.position = (x, y)

        # Create node theme
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvNode):
                color = self.agent_type_colors.get(agent_state.agent_type, [150, 150, 150, 255])
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, color, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, color, category=dpg.mvThemeCat_Nodes)

        # Create the node
        with dpg.node(
            label=f"{agent_state.agent_type} Agent: {agent_state.name}",
            tag=node_id,
            pos=agent_state.position,
            parent="agent_node_editor"
        ):
            dpg.bind_item_theme(node_id, node_theme)
            
            # Input attribute
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag=f"input_{agent_state.name}"):
                dpg.add_text("Input")
                
            # Static attributes for agent info
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                self._create_status_indicators(agent_state)

            # Output attribute
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=f"output_{agent_state.name}"):
                dpg.add_text("Output")

        self.nodes[agent_state.name] = node_id
        return node_id

    def _create_status_indicators(self, agent_state):
        """Create status indicators for the node"""
        status_colors = {
            "active": [0, 255, 0, 255],    # Green
            "idle": [150, 150, 150, 255],  # Gray
            "busy": [255, 165, 0, 255],    # Orange
            "error": [255, 0, 0, 255]      # Red
        }
        
        # Status indicator
        with dpg.group(horizontal=True):
            dpg.add_text("Status: ")
            dpg.add_text(
                agent_state.status,
                tag=f"status_text_{agent_state.name}",
                color=status_colors.get(agent_state.status.lower(), [255, 255, 255, 255])
            )

        # Current task
        dpg.add_text("Current Task:", tag=f"task_label_{agent_state.name}")
        dpg.add_text(
            agent_state.current_task or "None",
            tag=f"task_text_{agent_state.name}",
            wrap=300
        )

        # Performance metrics
        with dpg.group(horizontal=True):
            dpg.add_text("CPU: ")
            dpg.add_text(
                f"{agent_state.cpu_usage:.1f}%",
                tag=f"cpu_text_{agent_state.name}"
            )
        
        with dpg.group(horizontal=True):
            dpg.add_text("Memory: ")
            dpg.add_text(
                f"{agent_state.memory_usage:.1f}MB",
                tag=f"memory_text_{agent_state.name}"
            )

    def _on_node_connect(self, sender, app_data):
        """Handle connection between agent nodes"""
        source_attr_id, target_attr_id = app_data
        source_agent = source_attr_id.split('_')[1]
        target_agent = target_attr_id.split('_')[1]
        
        # Create the link
        dpg.add_node_link(source_attr_id, target_attr_id, parent=sender)
        
        # Notify about the new connection
        if hasattr(self, 'on_connection_change'):
            self.on_connection_change(source_agent, target_agent, "connect")

    def _on_node_disconnect(self, sender, app_data):
        """Handle disconnection between agent nodes"""
        source_attr_id, target_attr_id = app_data
        source_agent = source_attr_id.split('_')[1]
        target_agent = target_attr_id.split('_')[1]
        
        if hasattr(self, 'on_connection_change'):
            self.on_connection_change(source_agent, target_agent, "disconnect")

    def update_node(self, agent_state):
        """Update an existing node with new agent state"""
        if agent_state.name not in self.nodes:
            self._add_agent_node(agent_state)
            return

        node_id = self.nodes[agent_state.name]
        
        # Update status text and color
        status_colors = {
            "active": [0, 255, 0, 255],
            "idle": [150, 150, 150, 255],
            "busy": [255, 165, 0, 255],
            "error": [255, 0, 0, 255]
        }
        
        dpg.configure_item(
            f"status_text_{agent_state.name}",
            default_value=agent_state.status,
            color=status_colors.get(agent_state.status.lower(), [255, 255, 255, 255])
        )
        
        # Update other metrics
        dpg.set_value(f"task_text_{agent_state.name}", agent_state.current_task or "None")
        dpg.set_value(f"cpu_text_{agent_state.name}", f"{agent_state.cpu_usage:.1f}%")
        dpg.set_value(f"memory_text_{agent_state.name}", f"{agent_state.memory_usage:.1f}MB")