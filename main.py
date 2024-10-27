# main.py

import dearpygui.dearpygui as dpg
import tkinter as tk
from src.ui.monitor import AgentMonitoringSystem
from src.core.config import SystemConfig


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

def main():
    # Create DPG context first
    dpg.create_context()
    
    try:
        # Initialize system
        config = SystemConfig()
        monitor = AgentMonitoringSystem(config)
        width, height = get_screen_size_percentage()
        
        # Create viewport (moved from setup_ui)
        dpg.create_viewport(
            title="Agent Monitoring System",
            width=width,
            height=height
        )
        
        # Setup UI elements
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