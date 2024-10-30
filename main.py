# main.py
import sys
import logging
from src.ui.monitor import AgentMonitoringSystem
from src.ui.state.app_state import AppState
from src.ui.state.store import StateEvent

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    monitor = None
    
    try:
        # Create and initialize monitoring system
        monitor = AgentMonitoringSystem()
        
        # Set up UI
        monitor.setup_ui()
        
        # Example: Create a test agent with proper data structure
        monitor.app_state.state_store.update(
            StateEvent.AGENT_ADDED,
            {
                'name': 'test_researcher',
                'agent_id': 'test_researcher',
                'agent_type': 'Research',
                'status': 'idle',
                'current_task': None,
                'metrics': {
                    'cpu_usage': 0.0,
                    'memory_usage': 0.0,
                    'tasks_completed': 0
                },
                'position': (100, 100)
            }
        )
        
        # Run the application
        monitor.run()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        # Ensure cleanup only if monitor was created
        if monitor is not None:
            monitor.cleanup()

if __name__ == "__main__":
    main()