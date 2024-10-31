import dearpygui.dearpygui as dpg
from typing import Any
from src.ui.state.app_state import AppState
from src.ui.state.store import StateEvent

class SettingsPanel:
    """UI Component for managing configuration settings"""
    def __init__(self, parent_id: int, app_state: AppState):
        self.parent_id = parent_id
        self.app_state = app_state
        self.config = self.app_state.config_manager  # Direct reference for convenience
        self.visible = False
    
    def setup(self):
        """Initialize the settings panel"""
        with dpg.window(
            label="Settings",
            show=False,
            tag="settings_window",
            width=400,
            height=600,
            pos=(100, 100)
        ):
            with dpg.tab_bar():
                with dpg.tab(label="System"):
                    self._create_system_settings()
                
                with dpg.tab(label="UI"):
                    self._create_ui_settings()
                
                with dpg.tab(label="Agents"):
                    self._create_agent_settings()
    
    def _create_system_settings(self):
        """Create system settings controls"""
        dpg.add_text("System Configuration")
        dpg.add_separator()
        
        # Docker settings
        dpg.add_text("Docker Settings")
        dpg.add_input_text(
            label="Docker Image",
            default_value=self.config.system.docker_image,
            callback=lambda s, a: setattr(self.config.system, 'docker_image', a)
        )
        dpg.add_input_text(
            label="Memory Limit",
            default_value=self.config.system.container_memory_limit,
            callback=lambda s, a: setattr(self.config.system, 'container_memory_limit', a)
        )
        
        # Logging settings
        dpg.add_text("Logging Settings")
        dpg.add_combo(
            label="Log Level",
            items=["DEBUG", "INFO", "WARNING", "ERROR"],
            default_value=self.config.system.log_level,
            callback=lambda s, a: setattr(self.config.system, 'log_level', a)
        )
    
    def _create_ui_settings(self):
        """Create UI settings controls"""
        dpg.add_text("UI Configuration")
        dpg.add_separator()
        
        # Theme settings
        dpg.add_combo(
            label="Theme",
            items=["dark", "light"],
            default_value=self.config.ui.theme,
            callback=lambda s, a: setattr(self.config.ui, 'theme', a)
        )
        
        # Window settings
        dpg.add_input_int(
            label="Window Width",
            default_value=self.config.ui.window_width,
            callback=lambda s, a: setattr(self.config.ui, 'window_width', a)
        )
        dpg.add_input_int(
            label="Window Height",
            default_value=self.config.ui.window_height,
            callback=lambda s, a: setattr(self.config.ui, 'window_height', a)
        )
    
    def _create_agent_settings(self):
        """Create agent settings controls"""
        dpg.add_text("Agent Configuration")
        dpg.add_separator()
        
        # Agent selection
        agent_names = list(self.config.agent_configs.keys())
        dpg.add_combo(
            label="Select Agent",
            items=agent_names,
            callback=self._on_agent_select
        )
        
        # Agent settings (populated when agent is selected)
        dpg.add_group(tag="agent_settings_group")
    
    def _on_agent_select(self, sender, app_data):
        """Handle agent selection"""
        agent_config = self.config.get_agent_config(app_data)
        if not agent_config:
            return
            
        # Clear existing settings
        dpg.delete_item("agent_settings_group", children_only=True)
        
        with dpg.group(parent="agent_settings_group"):
            # Basic settings
            dpg.add_input_text(
                label="System Message",
                default_value=agent_config.get('system_message', ''),
                multiline=True,
                callback=lambda s, a: self._update_agent_config(app_data, 'system_message', a)
            )
            
            dpg.add_input_float(
                label="Temperature",
                default_value=agent_config.get('temperature', 0.7),
                callback=lambda s, a: self._update_agent_config(app_data, 'temperature', a)
            )
            
            # Resource limits
            dpg.add_input_text(
                label="Memory Limit",
                default_value=agent_config.get('memory_limit', '256m'),
                callback=lambda s, a: self._update_agent_config(app_data, 'memory_limit', a)
            )
            
            dpg.add_input_float(
                label="CPU Limit",
                default_value=agent_config.get('cpu_limit', 0.25),
                callback=lambda s, a: self._update_agent_config(app_data, 'cpu_limit', a)
            )
    
    def _update_agent_config(self, agent_name: str, key: str, value: Any):
        """Update agent configuration"""
        agent_config = self.config.get_agent_config(agent_name)
        if agent_config:
            agent_config[key] = value
            self.config.agent_configs[agent_name] = agent_config
            
            # Notify state store of change
            self.app_state.state_store.update(
                StateEvent.CONFIG_CHANGED,
                {
                    'agent_config': {
                        'name': agent_name,
                        key: value
                    }
                }
            )
    
    def show(self):
        """Show the settings panel"""
        dpg.show_item("settings_window")
        self.visible = True
    
    def hide(self):
        """Hide the settings panel"""
        dpg.hide_item("settings_window")
        self.visible = False
    
    def toggle(self):
        """Toggle settings panel visibility"""
        if self.visible:
            self.hide()
        else:
            self.show()