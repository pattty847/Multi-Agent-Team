# main.py
import dearpygui.dearpygui as dpg
from src.core.config import SystemConfig
from src.ui.monitor import AgentMonitoringSystem

def main():
    # Create DPG context first
    dpg.create_context()
    
    try:
        # Initialize system
        config = SystemConfig()
        
        # Create and run monitor with workflow management
        monitor = AgentMonitoringSystem(config)
        monitor.setup_ui()
        
        # Setup DPG
        dpg.setup_dearpygui()
        
        # Show the viewport
        dpg.show_viewport()
        
        # Start the main loop
        monitor.run()
        
    except Exception as e:
        print(f"Error during startup: {str(e)}")
        raise
    finally:
        dpg.destroy_context()

if __name__ == "__main__":
    main()