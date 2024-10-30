# src/ui/monitor.py
import dearpygui.dearpygui as dpg
import logging
from pathlib import Path
from typing import Optional

from src.ui.state.app_state import AppState
from src.ui.components.agent_list import AgentListView
from src.ui.components.metrics_view import MetricsView
from src.ui.components.node_editor import NodeEditorView
from src.ui.components.message_logger import MessageLogger
from src.ui.components.settings_panel import SettingsPanel
from src.ui.state.store import StateEvent

logger = logging.getLogger(__name__)

class AgentMonitoringSystem:
    """Main monitoring system that handles UI and agent tracking"""
    
    def __init__(self):
        # Initialize application state
        self.app_state = AppState()
        
        # Get configuration
        self.ui_config = self.app_state.config_manager.ui_config
        self.system_config = self.app_state.config_manager.system_config
        
        # Initialize components (will be set up in setup_ui)
        self.agent_list: Optional[AgentListView] = None
        self.metrics_view: Optional[MetricsView] = None
        self.node_editor: Optional[NodeEditorView] = None
        self.message_logger: Optional[MessageLogger] = None
        self.settings_panel: Optional[SettingsPanel] = None
        
        # Set up logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging based on system configuration"""
        log_config = {
            'level': getattr(logging, self.system_config.log_level),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'filename': self.system_config.log_file,
            'maxBytes': self.system_config.max_log_size,
            'backupCount': self.system_config.backup_count
        }
        
        logging.basicConfig(**log_config)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)

    def setup_ui(self):
        """Initialize the monitoring UI with DearPyGui"""
        try:
            logger.debug("Starting UI setup")
            dpg.create_context()
            # Create main window
            with dpg.window(
                label=self.ui_config.window_title,
                tag="primary_window",
                width=self.ui_config.window_width,
                height=self.ui_config.window_height,
                menubar=True
            ):
                # Setup menu bar
                self._setup_menu()
                
                # Main layout with horizontal split
                with dpg.group(horizontal=True):
                    # Left panel - Agent List and Controls
                    with dpg.child_window(width=int(self.ui_config.window_width * 0.25), height=-1) as left_panel:
                        # Initialize agent list
                        self.agent_list = AgentListView(left_panel)
                        self.agent_list.setup()
                    
                    # Right panel - Main content area
                    with dpg.child_window(width=-1, height=-1):
                        with dpg.tab_bar():
                            # Workflow Tab with Node Editor
                            with dpg.tab(label="Workflows"):
                                self.node_editor = NodeEditorView("workflows_tab", self.app_state)
                                self.node_editor.setup()
                            
                            # Metrics Tab
                            with dpg.tab(label="Metrics"):
                                self.metrics_view = MetricsView("metrics_tab", self.app_state)
                                self.metrics_view.setup()
                            
                            # Logs Tab
                            with dpg.tab(label="Logs"):
                                self.message_logger = MessageLogger("logs_tab", self.app_state)
                                self.message_logger.setup()
            
            # Initialize settings panel
            self.settings_panel = SettingsPanel("primary_window", self.app_state)
            self.settings_panel.setup()
            
            # Set as primary window
            dpg.set_primary_window("primary_window", True)
            
            # Register state change handlers
            self._setup_state_handlers()
            
        except Exception as e:
            logger.error(f"Error in setup_ui: {str(e)}")
            raise

    def _setup_menu(self):
        """Setup the menu bar"""
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(
                    label="Settings",
                    callback=lambda: self.settings_panel.toggle()
                )
                dpg.add_menu_item(
                    label="Exit",
                    callback=self.cleanup_and_exit
                )
                
            with dpg.menu(label="View"):
                dpg.add_menu_item(
                    label="Reset Layout",
                    callback=self.reset_layout
                )
                
            with dpg.menu(label="Help"):
                dpg.add_menu_item(
                    label="About",
                    callback=self.show_about
                )

    def _setup_state_handlers(self):
        """Setup handlers for state changes"""
        # Subscribe to agent updates
        self.app_state.state_store.subscribe(
            StateEvent.AGENT_UPDATED,
            self._handle_agent_update
        )
        
        # Subscribe to workflow updates
        self.app_state.state_store.subscribe(
            StateEvent.WORKFLOW_UPDATED,
            self._handle_workflow_update
        )
        
        # Subscribe to metric updates
        self.app_state.state_store.subscribe(
            StateEvent.METRICS_UPDATED,
            self._handle_metrics_update
        )
        
        # Subscribe to config changes
        self.app_state.state_store.subscribe(
            StateEvent.CONFIG_CHANGED,
            self._handle_config_change
        )

    def _handle_agent_update(self, data):
        """Handle agent state updates"""
        if self.agent_list:
            self.agent_list.update_agent(data)
        if self.node_editor:
            self.node_editor.update_node(data)

    def _handle_workflow_update(self, data):
        """Handle workflow state updates"""
        if self.node_editor:
            self.node_editor.update_workflow(data)

    def _handle_metrics_update(self, data):
        """Handle metrics updates"""
        if self.metrics_view:
            self.metrics_view.update_metrics(data)

    def _handle_config_change(self, data):
        """Handle configuration changes"""
        # Reload configurations
        self.ui_config = self.app_state.config_manager.ui_config
        self.system_config = self.app_state.config_manager.system_config
        
        # Update UI components if needed
        self.reset_layout()

    def run(self):
        """Main application loop"""
        try:
            logger.debug("Starting main loop")
            
            while dpg.is_dearpygui_running():
                # Process any pending state updates
                self.app_state.event_bus.process_events()
                
                # Render frame
                dpg.render_dearpygui_frame()
                
        except Exception as e:
            logger.error(f"Error in run method: {str(e)}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop event bus
            self.app_state.event_bus.stop()
            
            # Save configurations
            self.app_state.config_manager.save_all_configs()
            
            # Clean up DPG
            dpg.destroy_context()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def cleanup_and_exit(self):
        """Clean up and exit application"""
        self.cleanup()
        exit(0)

    def reset_layout(self):
        """Reset UI layout to default"""
        # Implement layout reset logic here
        pass

    def show_about(self):
        """Show about dialog"""
        with dpg.window(label="About", modal=True, show=True):
            dpg.add_text("Multi-Agent System Monitor")
            dpg.add_text(f"Version: {self.system_config.version}")
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("About"))
