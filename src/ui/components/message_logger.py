# src/ui/components/message_logger.py
import dearpygui.dearpygui as dpg
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field

@dataclass
class LogMessage:
    """Represents a single log message"""
    timestamp: datetime
    level: str
    source: str
    content: str
    color: tuple = field(default=(255, 255, 255, 255))

class MessageLogger:
    """Component for displaying and managing log messages"""
    def __init__(self, parent_id: int, app_state):
        self.parent_id = parent_id
        self.app_state = app_state
        self.messages: List[LogMessage] = []
        self.filter_settings = {
            "show_info": True,
            "show_warning": True,
            "show_error": True,
            "search_text": ""
        }
        self.max_messages = 1000
        
    def setup(self):
        """Initialize the message logging interface"""
        with dpg.child_window(label="Message Log", height=-1, parent=self.parent_id):
            # Control panel
            with dpg.group(horizontal=True):
                dpg.add_checkbox(
                    label="Info",
                    default_value=True,
                    callback=self._on_filter_change,
                    tag="show_info"
                )
                dpg.add_checkbox(
                    label="Warning",
                    default_value=True,
                    callback=self._on_filter_change,
                    tag="show_warning"
                )
                dpg.add_checkbox(
                    label="Error",
                    default_value=True,
                    callback=self._on_filter_change,
                    tag="show_error"
                )
                
                dpg.add_button(
                    label="Clear",
                    callback=self.clear_messages
                )
                
                dpg.add_input_text(
                    label="Search",
                    callback=self._on_search_change,
                    width=200,
                    tag="message_search"
                )
            
            # Message table
            with dpg.child_window(height=-1, width=-1):
                with dpg.table(
                    header_row=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    scrollY=True,
                    tag="message_table"
                ):
                    dpg.add_table_column(label="Time", width_fixed=True)
                    dpg.add_table_column(label="Level", width_fixed=True)
                    dpg.add_table_column(label="Source", width_fixed=True)
                    dpg.add_table_column(label="Message", width_stretch=True)

    def add_message(self, level: str, source: str, content: str):
        """Add a new message to the log"""
        message = LogMessage(
            timestamp=datetime.now(),
            level=level.upper(),
            source=source,
            content=content,
            color=self._get_level_color(level)
        )
        
        self.messages.append(message)
        
        # Trim old messages if needed
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            
        self._update_display()

    def clear_messages(self):
        """Clear all messages from the log"""
        self.messages.clear()
        self._update_display()

    def _get_level_color(self, level: str) -> tuple:
        """Get color for different message levels"""
        colors = {
            "info": (255, 255, 255, 255),    # White
            "warning": (255, 255, 0, 255),    # Yellow
            "error": (255, 0, 0, 255),        # Red
            "success": (0, 255, 0, 255)       # Green
        }
        return colors.get(level.lower(), (255, 255, 255, 255))

    def _should_show_message(self, message: LogMessage) -> bool:
        """Check if message should be displayed based on current filters"""
        # Check level filters
        if message.level == "INFO" and not self.filter_settings["show_info"]:
            return False
        if message.level == "WARNING" and not self.filter_settings["show_warning"]:
            return False
        if message.level == "ERROR" and not self.filter_settings["show_error"]:
            return False
            
        # Check search text
        if self.filter_settings["search_text"]:
            search_text = self.filter_settings["search_text"].lower()
            if search_text not in message.content.lower() and \
               search_text not in message.source.lower():
                return False
                
        return True

    def _update_display(self):
        """Update the message display table"""
        if not dpg.does_item_exist("message_table"):
            return
            
        # Clear existing rows
        for child in dpg.get_item_children("message_table", slot=1):
            dpg.delete_item(child)
            
        # Add filtered messages
        for message in filter(self._should_show_message, self.messages):
            with dpg.table_row(parent="message_table"):
                dpg.add_text(message.timestamp.strftime("%H:%M:%S"))
                dpg.add_text(message.level, color=message.color)
                dpg.add_text(message.source)
                dpg.add_text(message.content)

    def _on_filter_change(self, sender, app_data):
        """Handle filter checkbox changes"""
        self.filter_settings["show_info"] = dpg.get_value("show_info")
        self.filter_settings["show_warning"] = dpg.get_value("show_warning")
        self.filter_settings["show_error"] = dpg.get_value("show_error")
        self._update_display()

    def _on_search_change(self, sender, app_data):
        """Handle search text changes"""
        self.filter_settings["search_text"] = app_data
        self._update_display()