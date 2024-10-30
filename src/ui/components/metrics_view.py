import dearpygui.dearpygui as dpg
from typing import Dict
from datetime import datetime

import psutil

class MetricsView:
    def __init__(self, parent_id: int, app_state):
        self.parent_id = parent_id
        self.app_state = app_state
        self.performance_series = {}
        self.system_metrics = {}
        self.workflow_metrics = {}

    def setup(self):
        with dpg.child_window(label="System Metrics", height=-1, parent=self.parent_id):
            with dpg.tab_bar():
                self._setup_performance_tab()
                self._setup_agent_metrics_tab()
                self._setup_workflow_metrics_tab()

    def _setup_performance_tab(self):
        with dpg.tab(label="Performance"):
            with dpg.group(horizontal=True):
                with dpg.child_window(width=-1):
                    dpg.add_text("System Overview")
                    dpg.add_separator()
                    self.system_metrics = {
                        "cpu": dpg.add_text("CPU: 0%"),
                        "memory": dpg.add_text("Memory: 0 MB"),
                        "active_agents": dpg.add_text("Active Agents: 0"),
                        "active_workflows": dpg.add_text("Active Workflows: 0")
                    }

                    with dpg.plot(label="System Performance", height=200, width=-1, 
                                 tag="system_performance_plot"):
                        dpg.add_plot_legend()
                        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Usage %")
                        
                        self.performance_series = {
                            "cpu": dpg.add_line_series([], [], label="CPU Usage", parent=y_axis),
                            "memory": dpg.add_line_series([], [], label="Memory Usage", parent=y_axis)
                        }
    
    def _setup_agent_metrics_tab(self):
        with dpg.tab(label="Agent Metrics"):
            # Agent-specific metrics
            self.agent_metrics_window = dpg.add_child_window(height=-1)
    
    def _setup_workflow_metrics_tab(self):
        with dpg.tab(label="Workflow Metrics"):
            # Workflow statistics
            with dpg.child_window():
                self.workflow_metrics = {
                    "total": dpg.add_text("Total Workflows: 0"),
                    "active": dpg.add_text("Active: 0"),
                    "completed": dpg.add_text("Completed: 0"),
                    "failed": dpg.add_text("Failed: 0")
                }
                
                dpg.add_separator()
                dpg.add_text("Recent Workflow Completion Times")
                # Add a plot for workflow completion times
                with dpg.plot(label="Completion Times", height=150, width=-1):
                    dpg.add_plot_axis(dpg.mvXAxis, label="Workflow")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Time (s)")
                    self.workflow_time_plot = dpg.add_bar_series([], [], parent=dpg.last_item())

    def update_metrics(self):
        if hasattr(self, 'metrics_view'):
            metrics_data = {
                'cpu': psutil.cpu_percent(),
                'memory': psutil.Process().memory_info().rss / 1024 / 1024,
                'active_agents': len(self.agents),
                'active_workflows': self.metrics['active_workflows']
            }
            self.metrics_view.update_metrics(metrics_data)