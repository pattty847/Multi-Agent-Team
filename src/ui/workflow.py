import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

class WorkflowMonitor:
    def __init__(self):
        self.active_workflows: Dict[str, Dict] = {}
        self.selected_workflow_id: Optional[str] = None
        self.graph_view_id: Optional[int] = None
        self.timeline_view_id: Optional[int] = None

    def select_workflow_callback(self, sender, app_data, user_data):
        """Callback for when a workflow is selected in the UI"""
        self.selected_workflow_id = user_data
        self.update_views()

    def update_views(self):
        """Update both graph and timeline views based on selected workflow"""
        if self.selected_workflow_id and self.selected_workflow_id in self.active_workflows:
            workflow = self.active_workflows[self.selected_workflow_id]
            self.update_graph_view(workflow)
            self.update_timeline_view(workflow)

    def update_graph_view(self, workflow: Dict):
        """Update the graph visualization of agent interactions"""
        if not self.graph_view_id:
            return

        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes for each agent
        for agent in workflow['agents']:
            G.add_node(agent['name'], role=agent['role'])

        # Add edges for interactions
        for interaction in workflow['interactions']:
            G.add_edge(
                interaction['from'],
                interaction['to'],
                timestamp=interaction['timestamp']
            )

        # Clear previous graph
        dpg.delete_item(self.graph_view_id, children_only=True)

        # Create layout
        pos = nx.spring_layout(G)
        
        # Draw nodes
        for node in G.nodes():
            x, y = pos[node]
            dpg.draw_circle(
                center=[x * 100 + 200, y * 100 + 200],
                radius=20,
                fill=[0, 255, 0, 255],
                parent=self.graph_view_id
            )
            dpg.draw_text(
                pos=[x * 100 + 180, y * 100 + 190],
                text=node,
                parent=self.graph_view_id
            )

        # Draw edges
        for edge in G.edges():
            start_pos = pos[edge[0]]
            end_pos = pos[edge[1]]
            dpg.draw_line(
                p1=[start_pos[0] * 100 + 200, start_pos[1] * 100 + 200],
                p2=[end_pos[0] * 100 + 200, end_pos[1] * 100 + 200],
                color=[255, 255, 255, 255],
                parent=self.graph_view_id
            )

    def update_timeline_view(self, workflow: Dict):
        """Update the timeline visualization of agent activities"""
        if not self.timeline_view_id:
            return

        # Clear previous timeline
        dpg.delete_item(self.timeline_view_id, children_only=True)

        # Sort interactions by timestamp
        interactions = sorted(
            workflow['interactions'],
            key=lambda x: datetime.fromisoformat(x['timestamp'])
        )

        # Calculate timeline dimensions
        timeline_start = datetime.fromisoformat(interactions[0]['timestamp'])
        timeline_end = datetime.fromisoformat(interactions[-1]['timestamp'])
        total_duration = (timeline_end - timeline_start).total_seconds()

        # Draw timeline base
        dpg.draw_line(
            p1=[50, 250],
            p2=[550, 250],
            color=[255, 255, 255, 255],
            parent=self.timeline_view_id
        )

        # Draw interactions on timeline
        for idx, interaction in enumerate(interactions):
            timestamp = datetime.fromisoformat(interaction['timestamp'])
            position = (timestamp - timeline_start).total_seconds() / total_duration
            x_pos = 50 + position * 500

            # Draw marker
            dpg.draw_circle(
                center=[x_pos, 250],
                radius=5,
                fill=[0, 255, 0, 255],
                parent=self.timeline_view_id
            )

            # Draw label
            dpg.draw_text(
                pos=[x_pos - 20, 260],
                text=f"{interaction['from']} → {interaction['to']}",
                parent=self.timeline_view_id
            )

    def register_workflow(self, workflow_id: str, workflow_data: Dict):
        """Register a new workflow to be monitored"""
        self.active_workflows[workflow_id] = workflow_data
        if not self.selected_workflow_id:
            self.selected_workflow_id = workflow_id
            self.update_views()

    def update_workflow(self, workflow_id: str, workflow_data: Dict):
        """Update an existing workflow's data"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id] = workflow_data
            if workflow_id == self.selected_workflow_id:
                self.update_views()