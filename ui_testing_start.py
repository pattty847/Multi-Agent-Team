import dearpygui.dearpygui as dpg
import threading
from typing import Dict
import time
import logging
from autogen import GroupChat
from src.agents.monitored_agent import TeamConfiguration
from src.ui.workflow_monitor import WorkflowMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentWorkflowApp:
    def __init__(self):
        self.workflow_monitor = WorkflowMonitor()
        self.active_teams: Dict[str, GroupChat] = {}
        self.is_running = False

    def setup_ui(self):
        """Initialize the UI components"""
        logger.info("Setting up UI...")
        
        dpg.create_context()
        
        # Setup theme
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 15, 15))
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (30, 30, 30))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255))
        
        dpg.bind_theme(global_theme)
        
        # Create viewport
        dpg.create_viewport(
            title="AI Agent Workflow Monitor",
            width=1200,
            height=800,
            resizable=True
        )

        # Create main window
        with dpg.window(
            label="AI Agent Workflow Monitor",
            tag="main_window",
            pos=(0, 0),
            width=1200,
            height=800,
            no_close=True
        ):
            # Left panel for workflow selection and stats
            with dpg.group(horizontal=False, width=300):
                dpg.add_text("Active Workflows")
                self.workflow_list = dpg.add_listbox(
                    tag="workflow_list",
                    items=[],
                    callback=self.workflow_monitor.select_workflow_callback,
                    width=280,
                    num_items=10
                )

                dpg.add_separator()
                dpg.add_text("System Statistics")
                self.stats_group = dpg.add_group(tag="stats_group")

            # Right panel for visualizations
            with dpg.group(horizontal=False):
                with dpg.tab_bar():
                    with dpg.tab(label="Graph View"):
                        self.workflow_monitor.graph_view_id = dpg.add_drawlist(
                            width=800,
                            height=600,
                            tag="graph_view"
                        )
                    with dpg.tab(label="Timeline"):
                        self.workflow_monitor.timeline_view_id = dpg.add_drawlist(
                            width=800,
                            height=600,
                            tag="timeline_view"
                        )

        # Configure viewport
        dpg.set_primary_window("main_window", True)
        logger.info("UI setup complete")

    def update_workflow_list(self):
        """Update the workflow list in the UI"""
        items = list(self.workflow_monitor.active_workflows.keys())
        dpg.configure_item("workflow_list", items=items)

    def update_stats(self):
        """Update system statistics"""
        try:
            dpg.delete_item("stats_group", children_only=True)
            with dpg.group(parent="stats_group"):
                dpg.add_text(f"Active Teams: {len(self.active_teams)}")
                dpg.add_text(f"Total Messages: {self.count_total_messages()}")
                dpg.add_text(f"Active Agents: {self.count_active_agents()}")
        except Exception as e:
            logger.error(f"Error updating stats: {e}")

    def count_total_messages(self) -> int:
        """Count total messages across all workflows"""
        total = 0
        for workflow in self.workflow_monitor.active_workflows.values():
            total += len(workflow.get('interactions', []))
        return total

    def count_active_agents(self) -> int:
        """Count total unique agents across all workflows"""
        agents = set()
        for workflow in self.workflow_monitor.active_workflows.values():
            for agent in workflow.get('agents', []):
                agents.add(agent['name'])
        return len(agents)

    def start_demo_workflow(self):
        """Start a demo workflow to showcase the UI"""
        logger.info("Starting demo workflows...")
        
        # Create a research team
        team_config = TeamConfiguration(self.workflow_monitor)
        research_team = team_config.create_research_team()
        self.active_teams[team_config.workflow_id] = research_team

        # Update UI
        self.update_workflow_list()
        
        # Start the research workflow in a separate thread
        def run_research():
            try:
                researcher = research_team.agent_by_name("Researcher")
                researcher.initiate_chat(
                    research_team.agent_by_name("Analyst"),
                    message="Can you help analyze the impact of AI on workplace productivity?"
                )
            except Exception as e:
                logger.error(f"Error in research workflow: {e}")

        research_thread = threading.Thread(target=run_research, daemon=True)
        research_thread.start()

        # Create a development team after a delay
        time.sleep(2)
        team_config = TeamConfiguration(self.workflow_monitor)
        dev_team = team_config.create_development_team()
        self.active_teams[team_config.workflow_id] = dev_team

        # Update UI
        self.update_workflow_list()

        # Start the development workflow
        def run_development():
            try:
                architect = dev_team.agent_by_name("Architect")
                architect.initiate_chat(
                    dev_team.agent_by_name("Developer"),
                    message="Let's design a new microservice for user authentication."
                )
            except Exception as e:
                logger.error(f"Error in development workflow: {e}")

        dev_thread = threading.Thread(target=run_development, daemon=True)
        dev_thread.start()
        
        logger.info("Demo workflows started")

    def run(self):
        """Start the application"""
        try:
            logger.info("Starting application...")
            self.setup_ui()
            
            # Show viewport
            dpg.show_viewport()
            dpg.setup_dearpygui()
            
            # Start demo workflows after a short delay
            threading.Timer(1.0, self.start_demo_workflow).start()
            
            # Main application loop
            self.is_running = True
            while self.is_running and dpg.is_dearpygui_running():
                self.update_stats()
                dpg.render_dearpygui_frame()
                time.sleep(0.1)  # Add a small delay to prevent high CPU usage
                
            logger.info("Application shutdown initiated")
            dpg.destroy_context()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise

def main():
    try:
        logger.info("Initializing application...")
        app = AgentWorkflowApp()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()