import logging
import dearpygui.dearpygui as dpg
from typing import Dict, List
from datetime import datetime

import psutil

logger = logging.getLogger(__name__)

class MetricsView:
    def __init__(self, parent_id: int, app_state):
        self.parent_id = parent_id
        self.app_state = app_state
        self.performance_data: List[Dict] = []
        self.max_data_points = 100
        
    def setup(self):
        """Initialize the metrics view interface"""
        with dpg.child_window(label="Metrics", parent=self.parent_id):
            with dpg.tab_bar():
                # Performance Tab
                with dpg.tab(label="Performance"):
                    self._setup_performance_view()
                
                # Agent Metrics Tab
                with dpg.tab(label="Agent Metrics"):
                    self._setup_agent_metrics()
                
                # Workflow Metrics Tab
                with dpg.tab(label="Workflow Metrics"):
                    self._setup_workflow_metrics()

    def _setup_performance_view(self):
        """Setup system performance overview"""
        with dpg.group():
            dpg.add_text("System Overview")
            dpg.add_separator()
            
            # System metrics
            with dpg.group():
                self.cpu_text = dpg.add_text("CPU: 0%")
                self.memory_text = dpg.add_text("Memory: 0 MB")
                self.active_agents_text = dpg.add_text("Active Agents: 0")
                self.active_workflows_text = dpg.add_text("Active Workflows: 0")
            
            # Performance plot
            with dpg.plot(label="System Performance", height=300, width=-1):
                # Legends
                dpg.add_plot_legend()
                
                # Axes
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                
                with dpg.plot_axis(dpg.mvYAxis, label="Usage %"):
                    # Create series for CPU and memory
                    self.cpu_series = dpg.add_line_series([], [], label="CPU Usage")
                    self.memory_series = dpg.add_line_series([], [], label="Memory Usage")

    def _setup_agent_metrics(self):
        """Setup agent-specific metrics view"""
        with dpg.group():
            dpg.add_text("Agent Performance")
            dpg.add_separator()
            
            # Agent metrics table
            with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                          borders_innerV=True, borders_outerV=True, scrollY=True):
                
                dpg.add_table_column(label="Agent")
                dpg.add_table_column(label="Type")
                dpg.add_table_column(label="Status")
                dpg.add_table_column(label="CPU %")
                dpg.add_table_column(label="Memory MB")
                dpg.add_table_column(label="Tasks Done")
                
                # Table will be populated dynamically

    def _setup_workflow_metrics(self):
        """Setup workflow metrics view"""
        with dpg.group():
            # Workflow statistics
            with dpg.group():
                self.total_workflows = dpg.add_text("Total Workflows: 0")
                self.active_workflows = dpg.add_text("Active: 0")
                self.completed_workflows = dpg.add_text("Completed: 0")
                self.failed_workflows = dpg.add_text("Failed: 0")
            
            dpg.add_separator()
            dpg.add_text("Recent Workflow Completion Times")
            
            # Workflow completion time plot
            with dpg.plot(label="Completion Times", height=200, width=-1):
                dpg.add_plot_axis(dpg.mvXAxis, label="Workflow")
                with dpg.plot_axis(dpg.mvYAxis, label="Time (s)"):
                    self.completion_series = dpg.add_bar_series([], [])

    def update_metrics(self):
        """Update all metrics displays"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)  # Convert to MB
            
            # Update performance data
            self.performance_data.append({
                'cpu': cpu_percent,
                'memory': memory_usage,
                'timestamp': datetime.now()
            })
            
            # Trim data if needed
            if len(self.performance_data) > self.max_data_points:
                self.performance_data = self.performance_data[-self.max_data_points:]
            
            # Update text displays
            dpg.set_value(self.cpu_text, f"CPU: {cpu_percent:.1f}%")
            dpg.set_value(self.memory_text, f"Memory: {memory_usage:.1f} MB")
            
            # Update plots
            times = list(range(len(self.performance_data)))
            cpu_values = [d['cpu'] for d in self.performance_data]
            memory_values = [d['memory'] for d in self.performance_data]
            
            dpg.set_value(self.cpu_series, [times, cpu_values])
            dpg.set_value(self.memory_series, [times, memory_values])
            
            # Update agent metrics from app state
            self._update_agent_table()
            
            # Update workflow metrics
            self._update_workflow_metrics()
            
            logger.debug("Metrics updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")

    def _update_agent_table(self):
        """Update the agent metrics table"""
        # Clear existing rows
        for child in dpg.get_item_children(self.agent_table_id, slot=1):
            dpg.delete_item(child)
            
        # Add row for each agent
        for agent in self.app_state.get_agents():
            with dpg.table_row():
                dpg.add_text(agent.name)
                dpg.add_text(agent.agent_type)
                dpg.add_text(agent.status)
                dpg.add_text(f"{agent.cpu_usage:.1f}%")
                dpg.add_text(f"{agent.memory_usage:.1f}")
                dpg.add_text(str(agent.tasks_completed))

    def _update_workflow_metrics(self):
        """Update workflow metrics displays"""
        workflows = self.app_state.get_workflows()
        
        # Update counts
        total = len(workflows)
        active = sum(1 for w in workflows if w['status'] == 'active')
        completed = sum(1 for w in workflows if w['status'] == 'completed')
        failed = sum(1 for w in workflows if w['status'] == 'failed')
        
        dpg.set_value(self.total_workflows, f"Total Workflows: {total}")
        dpg.set_value(self.active_workflows, f"Active: {active}")
        dpg.set_value(self.completed_workflows, f"Completed: {completed}")
        dpg.set_value(self.failed_workflows, f"Failed: {failed}")
        
        # Update completion times plot
        completed_workflows = [w for w in workflows if w['status'] == 'completed']
        if completed_workflows:
            indices = list(range(len(completed_workflows)))
            times = [w['completion_time'] for w in completed_workflows]
            dpg.set_value(self.completion_series, [indices, times])