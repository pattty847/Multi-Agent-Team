# src/ui/monitor.py
import os
import dearpygui.dearpygui as dpg
import logging
from pathlib import Path
from typing import Optional

from src.config.config_manager import ConfigManager
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
        self.config = self.app_state.config_manager
        
        # Set up logging based on system config
        self._setup_logging()
        
        # Initialize components (will be set up in setup_ui)
        self.agent_list: Optional[AgentListView] = None
        self.metrics_view: Optional[MetricsView] = None
        self.node_editor: Optional[NodeEditorView] = None
        self.message_logger: Optional[MessageLogger] = None

    def _setup_logging(self):
        """Configure logging based on system configuration"""
        log_config = {
            'level': getattr(logging, self.config.system.log_level),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'filename': self.config.system.log_file,
            'maxBytes': self.config.system.max_log_size,
            'backupCount': self.config.system.backup_count
        }
        
        # Create log directory if needed
        log_path = Path(log_config['filename']).parent
        log_path.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(**log_config)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)
        
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized")

    def _setup_dpg(self):
        """Setup DearPyGui context and windows"""
        dpg.create_context()
        
        # Configure window based on UI config
        self.viewport = dpg.create_viewport(
            title=self.config.ui.window_title,
            width=int(self.config.ui.window_width * self.config.ui.window_resulution_pct),
            height=int(self.config.ui.window_height * self.config.ui.window_resulution_pct)
        )
        
        # Set DPI scale if specified
        if hasattr(self.config.ui, 'dpi_scale'):
            dpg.set_global_font_scale(self.config.ui.dpi_scale)
        
        # Set initial window position if specified
        if hasattr(self.config.ui, 'window_pos_x') and hasattr(self.config.ui, 'window_pos_y'):
            dpg.set_viewport_pos(
                [self.config.ui.window_pos_x, 
                 self.config.ui.window_pos_y]
            )
        
        # Maximize if configured
        if getattr(self.config.ui, 'window_is_maximized', False):
            dpg.maximize_viewport()
        
        self._setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        # Set the primary window
        dpg.set_primary_window("primary_window", True)

    def _get_openai_key(self) -> str:
        """Get OpenAI API key from environment with fallback to config"""
        key = os.getenv('OPENAI_API_KEY')
        if not key:
            key = self.config.system.openai_api_key
            if key.startswith('${') and key.endswith('}'):
                # If still using variable syntax in config, warn and return empty
                logger.warning("OpenAI API key not found in environment variables")
                return ''
        return key

    def _setup_ui(self):
        try:
            logger.debug("Starting UI setup")
            # Create main window
            with dpg.window(
                label=self.config.ui.window_title,
                tag="primary_window",
                width=int(self.config.ui.window_width * self.config.ui.window_resulution_pct),
                height=int(self.config.ui.window_height * self.config.ui.window_resulution_pct),
                menubar=True
            ):
                # Setup menu bar
                self._setup_menu()
                
                # Main layout with horizontal split
                with dpg.group(horizontal=True):
                    # Left panel - Agent List and Controls
                    with dpg.child_window(
                        width=int(self.config.ui.window_width * 0.20),
                        height=-1
                    ) as left_panel:
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
        self.config = self.app_state.config_manager
        
        # Update UI components if needed
        self.reset_layout()

    def run(self):
        """Run the monitoring system"""
        try:
            # Ensure OpenAI key is available
            if not self._get_openai_key():
                logger.error("No OpenAI API key found. Please set OPENAI_API_KEY environment variable")
                return
            
            # Start the UI
            self._setup_dpg()
            
            # Start event loop
            dpg.start_dearpygui()
            
        except Exception as e:
            logger.error(f"Error running monitoring system: {str(e)}")
            raise
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.cleanup_and_exit()
            dpg.destroy_context()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

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
            dpg.add_text(f"Version: {getattr(self.config.system, 'version', 'N/A')}")
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item("About"))
