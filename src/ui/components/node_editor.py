import dearpygui.dearpygui as dpg
from typing import Dict, Optional, Tuple, List, Set
import logging
from datetime import datetime

from src.ui.state.app_state import AppState
from src.ui.state.store import StateEvent

logger = logging.getLogger(__name__)

class NodeEditorView:
    """Enhanced interactive node editor for visualizing and managing agent connections"""
    
    def __init__(self, parent_id: int, app_state: AppState):
        self.parent_id = parent_id
        self.app_state = app_state
        self.nodes: Dict[str, int] = {}  # Maps agent_id to node_id
        self.node_positions: Dict[str, Tuple[int, int]] = {}  # Stores node positions
        self.connections: Set[Tuple[str, str]] = set()  # Tracks active connections
        self.selected_node: Optional[str] = None
        self.is_dragging = False
        self.context_node = None  # For context menu
        
        # Node styling configurations
        self.node_colors = {
            "Research": (0, 150, 255, 255),    # Blue
            "Code": (0, 255, 150, 255),        # Green
            "Viz": (255, 150, 0, 255),         # Orange
            "QA": (255, 0, 150, 255),          # Pink
            "PM": (150, 0, 255, 255),          # Purple
            "default": (150, 150, 150, 255)    # Gray
        }
        
        self.status_colors = {
            "active": (0, 255, 0, 255),      # Green
            "idle": (150, 150, 150, 255),    # Gray
            "busy": (255, 165, 0, 255),      # Orange
            "error": (255, 0, 0, 255),       # Red
            "default": (255, 255, 255, 255)  # White
        }
        
    def _subscribe_to_events(self):
        """Initialize the node editor interface"""
        # Subscribe to agent added event
        self.app_state.state_store.subscribe(
            StateEvent.AGENT_ADDED,
            self._handle_agent_added
        )
        
    def _handle_agent_added(self, agent_data):
        """Handle agent added event"""
        agent_id = agent_data.get('agent_id')
        agent_type = agent_data.get('agent_type')
        position = agent_data.get('position', None)
        
        # Add the node to the editor
        self.add_node(agent_id, agent_type, position)

    def setup(self):
        self._subscribe_to_events()
        """Initialize the node editor interface"""
        # Create node editor
        with dpg.node_editor(
            callback=self._on_node_connect,
            delink_callback=self._on_node_disconnect,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            tag="agent_node_editor",
            parent=self.parent_id
        ):
            pass  # Nodes will be added dynamically

        # Setup node context menu
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, 
                                      callback=self._show_context_menu)

        # Create context menu
        with dpg.window(
            label="Node Menu",
            modal=True,
            show=False,
            id="node_context_menu",
            no_title_bar=True,
            no_resize=True,
            no_move=True
        ):
            dpg.add_button(label="View Details", callback=self._show_node_details)
            dpg.add_button(label="Reset Position", callback=self._reset_node_position)
            dpg.add_button(label="Delete Node", callback=self._delete_node)

        # Create node details window
        with dpg.window(
            label="Node Details",
            show=False,
            tag="node_details_window",
            width=400,
            height=500,
            pos=(100, 100)
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Agent ID: ")
                dpg.add_text("", tag="details_agent_id")
            
            with dpg.group(horizontal=True):
                dpg.add_text("Type: ")
                dpg.add_text("", tag="details_type")
            
            with dpg.group(horizontal=True):
                dpg.add_text("Status: ")
                dpg.add_text("", tag="details_status")
            
            # Performance metrics
            with dpg.collapsing_header(label="Performance Metrics", default_open=True):
                dpg.add_simple_plot(
                    label="CPU Usage",
                    tag="cpu_plot",
                    height=100
                )
                dpg.add_simple_plot(
                    label="Memory Usage",
                    tag="memory_plot",
                    height=100
                )
            
            # Task history
            with dpg.collapsing_header(label="Task History", default_open=True):
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Time")
                    dpg.add_table_column(label="Task")
                    dpg.add_table_column(label="Status")

    def add_node(self, agent_id: str, agent_type: str, position: Optional[Tuple[int, int]] = None) -> int:
        """Add a new agent node to the editor"""
        if agent_id in self.nodes:
            logger.warning(f"Node for agent {agent_id} already exists")
            return self.nodes[agent_id]

        # Calculate position if not provided
        if position is None:
            position = self._calculate_new_node_position()
        
        self.node_positions[agent_id] = position

        # Create node theme
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvNode):
                color = self.node_colors.get(agent_type, self.node_colors["default"])
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, color)
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, color)

        # Create the node
        with dpg.node(
            label=f"{agent_type}: {agent_id}",
            pos=position,
            parent="agent_node_editor"
        ) as node_id:
            # Bind theme
            dpg.bind_item_theme(node_id, node_theme)
            
            # Input attribute for connections
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input,
                tag=f"input_{agent_id}"
            ):
                dpg.add_text("Input")
            
            # Status indicator
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group(horizontal=True):
                    dpg.add_text("Status: ")
                    dpg.add_text(
                        "Idle",
                        tag=f"status_{agent_id}",
                        color=self.status_colors["idle"]
                    )
            
            # Quick stats
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text("", tag=f"stats_{agent_id}")
            
            # Output attribute for connections
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                tag=f"output_{agent_id}"
            ):
                dpg.add_text("Output")

        # Store node reference
        self.nodes[agent_id] = node_id
        return node_id

    def update_node(self, agent_data: Dict):
        """Update node with new agent data"""
        agent_id = agent_data.get("id")
        if not agent_id or agent_id not in self.nodes:
            logger.warning(f"Cannot update node: {agent_id} not found")
            return

        # Update status
        status = agent_data.get("status", "idle").lower()
        status_color = self.status_colors.get(status, self.status_colors["default"])
        dpg.configure_item(
            f"status_{agent_id}",
            default_value=status.capitalize(),
            color=status_color
        )

        # Update quick stats
        stats_text = (
            f"CPU: {agent_data.get('cpu_usage', 0):.1f}%\n"
            f"Memory: {agent_data.get('memory_usage', 0):.1f}MB\n"
            f"Tasks: {agent_data.get('tasks_completed', 0)}"
        )
        dpg.configure_item(f"stats_{agent_id}", default_value=stats_text)

        # Update position if changed
        if "position" in agent_data:
            self.node_positions[agent_id] = agent_data["position"]
            dpg.configure_item(self.nodes[agent_id], pos=agent_data["position"])

    def _calculate_new_node_position(self) -> Tuple[int, int]:
        """Calculate position for a new node"""
        num_nodes = len(self.nodes)
        x = 100 + (num_nodes % 3) * 250  # 3 columns
        y = 100 + (num_nodes // 3) * 200  # 200px vertical spacing
        return (x, y)

    def _on_node_connect(self, sender, app_data):
        """Handle connection between nodes"""
        source_attr, target_attr = app_data
        source_id = source_attr.split('_')[1]
        target_id = target_attr.split('_')[1]

        # Add to connections set
        self.connections.add((source_id, target_id))
        
        # Notify app state of new connection
        self.app_state.state_store.update(
            "AGENT_CONNECTION_ADDED",
            {
                "source": source_id,
                "target": target_id,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _on_node_disconnect(self, sender, app_data):
        """Handle disconnection between nodes"""
        source_attr, target_attr = app_data
        source_id = source_attr.split('_')[1]
        target_id = target_attr.split('_')[1]

        # Remove from connections set
        self.connections.discard((source_id, target_id))
        
        # Notify app state
        self.app_state.state_store.update(
            "AGENT_CONNECTION_REMOVED",
            {
                "source": source_id,
                "target": target_id,
                "timestamp": datetime.now().isoformat()
            }
        )

    def _show_context_menu(self, sender, app_data):
        """Show context menu for node"""
        if dpg.is_item_hovered("agent_node_editor"):
            mouse_pos = dpg.get_mouse_pos()
            
            # Find closest node
            closest_node = None
            min_distance = float('inf')
            
            for agent_id, pos in self.node_positions.items():
                dx = mouse_pos[0] - pos[0]
                dy = mouse_pos[1] - pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                
                if distance < min_distance and distance < 50:  # Within 50 pixels
                    min_distance = distance
                    closest_node = agent_id
            
            if closest_node:
                self.context_node = closest_node
                dpg.configure_item("node_context_menu", show=True, pos=mouse_pos)

    def _show_node_details(self):
        """Show detailed information about a node"""
        if not self.context_node:
            return

        # Get agent data from app state
        agent_data = self.app_state.state_store.get_state()["agents"].get(self.context_node)
        if not agent_data:
            return

        # Update details window
        dpg.configure_item("node_details_window", show=True)
        dpg.set_value("details_agent_id", self.context_node)
        dpg.set_value("details_type", agent_data.get("type", "Unknown"))
        dpg.set_value("details_status", agent_data.get("status", "Unknown"))

        # Update performance plots
        if "performance_history" in agent_data:
            cpu_history = [p["cpu"] for p in agent_data["performance_history"]]
            mem_history = [p["memory"] for p in agent_data["performance_history"]]
            
            dpg.configure_item("cpu_plot", values=cpu_history)
            dpg.configure_item("memory_plot", values=mem_history)

    def _reset_node_position(self):
        """Reset node position to default"""
        if self.context_node:
            new_pos = self._calculate_new_node_position()
            self.node_positions[self.context_node] = new_pos
            dpg.configure_item(self.nodes[self.context_node], pos=new_pos)

    def _delete_node(self):
        """Delete node and its connections"""
        if not self.context_node:
            return

        # Remove connections involving this node
        self.connections = {
            (s, t) for s, t in self.connections
            if s != self.context_node and t != self.context_node
        }

        # Remove node
        dpg.delete_item(self.nodes[self.context_node])
        del self.nodes[self.context_node]
        del self.node_positions[self.context_node]
        
        # Notify app state
        self.app_state.state_store.update(
            "AGENT_REMOVED",
            {
                "agent_id": self.context_node,
                "timestamp": datetime.now().isoformat()
            }
        )

        self.context_node = None
        dpg.configure_item("node_context_menu", show=False)