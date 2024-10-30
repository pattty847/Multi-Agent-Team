# src/ui/state/event_bus.py
from typing import Dict, List, Callable
from enum import Enum, auto
from queue import Queue, Empty
import threading
import time

class EventType(Enum):
    """System event types"""
    AGENT_MESSAGE = auto()
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    ERROR_OCCURRED = auto()
    RESOURCE_LIMIT = auto()
    SYSTEM_STATUS = auto()

class Event:
    """Represents a system event"""
    def __init__(self, type: EventType, data: Dict, source: str):
        self.type = type
        self.data = data
        self.source = source
        self.timestamp = time.time()

class EventBus:
    """Event bus for system-wide communication"""
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {
            event: [] for event in EventType
        }
        self._queue = Queue()
        self._running = False
        self._thread = None

    def start(self):
        """Start event processing"""
        self._running = True
        self._thread = threading.Thread(target=self.process_events)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """Stop event processing"""
        self._running = False
        if self._thread:
            self._thread.join()

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to events of a specific type"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from events"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event: Event):
        """Publish an event to subscribers"""
        self._queue.put(event)

    def process_events(self):
        """Process events from queue"""
        while self._running:
            try:
                event = self._queue.get(timeout=0.1)
                self._notify_subscribers(event)
                self._queue.task_done()
            except Empty:  # Using the imported Empty exception
                continue
            except Exception as e:
                print(f"Error processing event: {e}")

    def _notify_subscribers(self, event: Event):
        """Notify subscribers of an event"""
        for callback in self._subscribers[event.type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event subscriber: {e}")