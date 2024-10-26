# main.py
import logging
from src.config import SystemConfig
from src.ui.monitor import AgentMonitor

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize configuration
        config = SystemConfig()
        
        # Create and run monitor with workflow management
        monitor = AgentMonitor(config)
        monitor.setup_ui()
        monitor.run()
        
    except Exception as e:
        logging.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()