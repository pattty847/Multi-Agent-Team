# src/ui/state/app_state.py
from src.config.config_manager import ConfigManager
from src.ui.state.store import StateStore, StateEvent
from src.ui.state.event_bus import EventBus, EventType, Event

class AppState:
    """Central application state management"""
    def __init__(self):
        # Initialize core components
        self.config_manager = ConfigManager()
        self.state_store = StateStore()
        self.event_bus = EventBus()
                
        # Set up event handlers
        self._setup_event_handlers()
        
        # Start event bus
        self.event_bus.start()
    
    def _setup_event_handlers(self):
        """Set up handlers for various events"""
        # Handle configuration changes
        self.state_store.subscribe(
            StateEvent.CONFIG_CHANGED,
            self._handle_config_change
        )
        
        # Handle agent events
        self.event_bus.subscribe(
            EventType.AGENT_MESSAGE,
            self._handle_agent_message
        )
        
        self.event_bus.subscribe(
            EventType.RESOURCE_LIMIT,
            self._handle_resource_limit
        )
    
    def _handle_config_change(self, data):
        """Handle configuration changes"""
        if 'agent_config' in data:
            # Update agent configuration
            self.config_manager.update_agent_config(
                data['agent_config']['name'],
                **data['agent_config']
            )
            
        elif 'ui_config' in data:
            # Update UI configuration and save
            for key, value in data['ui_config'].items():
                if hasattr(self.config_manager.ui_config, key):
                    setattr(self.config_manager.ui_config, key, value)
            self.config_manager.ui_config.save_config()
            
        # Notify components of config change
        self.event_bus.publish(Event(
            type=EventType.SYSTEM_STATUS,
            data={'config_updated': True},
            source='app_state'
        ))
    
    def _handle_agent_message(self, event: Event):
        """Handle messages from agents"""
        # Update agent state
        self.state_store.update(
            StateEvent.AGENT_UPDATED,
            {
                'agent_id': event.data['agent_id'],
                'message': event.data['message'],
                'timestamp': event.timestamp
            }
        )
    
    def _handle_resource_limit(self, event: Event):
        """Handle resource limit warnings"""
        agent_config = self.config_manager.get_agent_config(event.data['agent_id'])
        if agent_config:
            # Adjust resource limits if needed
            if event.data['resource'] == 'memory':
                new_limit = f"{int(agent_config.memory_limit[:-1]) * 1.5}m"
                self.config_manager.update_agent_config(
                    event.data['agent_id'],
                    memory_limit=new_limit
                )
            elif event.data['resource'] == 'cpu':
                new_limit = agent_config.cpu_limit * 1.5
                self.config_manager.update_agent_config(
                    event.data['agent_id'],
                    cpu_limit=new_limit
                )