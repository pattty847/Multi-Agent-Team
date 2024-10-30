# src/ui/state/store.py
from typing import Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

class StateEvent(Enum):
    """Enum for different state change events"""
    AGENT_ADDED = auto()
    AGENT_UPDATED = auto()
    AGENT_REMOVED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_UPDATED = auto()
    WORKFLOW_ENDED = auto()
    METRICS_UPDATED = auto()
    CONFIG_CHANGED = auto()

@dataclass
class StateChange:
    """Represents a state change event"""
    event_type: StateEvent
    data: Any
    timestamp: datetime = datetime.now()

class StateStore:
    """Central state management store"""
    def __init__(self):
        self._state = {
            "agents": {},
            "workflows": {},
            "metrics": {},
            "config": {}
        }
        self._subscribers: Dict[StateEvent, List[Callable]] = {
            event: [] for event in StateEvent
        }
        self._history: List[StateChange] = []

    def subscribe(self, event_type: StateEvent, callback: Callable):
        """Subscribe to state changes for a specific event type"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: StateEvent, callback: Callable):
        """Unsubscribe from state changes"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def update(self, event_type: StateEvent, data: Dict):
        """Update state and notify subscribers"""
        self._update_state(event_type, data)
        self._notify(event_type, data)
        self._record_change(event_type, data)

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return self._state.copy()

    def get_history(self) -> List[StateChange]:
        """Get state change history"""
        return self._history.copy()

    def _update_state(self, event_type: StateEvent, data: Dict):
        """Update internal state based on event type"""
        if event_type == StateEvent.AGENT_ADDED:
            agent_id = data.get('name') or data.get('agent_id')
            if agent_id:
                self._state["agents"][agent_id] = data
        elif event_type == StateEvent.AGENT_UPDATED:
            agent_id = data.get('name') or data.get('agent_id')
            if agent_id and agent_id in self._state["agents"]:
                self._state["agents"][agent_id].update(data)
        elif event_type == StateEvent.AGENT_REMOVED:
            agent_id = data.get('name') or data.get('agent_id')
            if agent_id:
                self._state["agents"].pop(agent_id, None)
        elif event_type == StateEvent.WORKFLOW_STARTED:
            workflow_id = data.get('id')
            if workflow_id:
                self._state["workflows"][workflow_id] = data
        elif event_type == StateEvent.WORKFLOW_UPDATED:
            workflow_id = data.get('id')
            if workflow_id and workflow_id in self._state["workflows"]:
                self._state["workflows"][workflow_id].update(data)
        elif event_type == StateEvent.WORKFLOW_ENDED:
            workflow_id = data.get('id')
            if workflow_id:
                self._state["workflows"].pop(workflow_id, None)
        elif event_type == StateEvent.METRICS_UPDATED:
            self._state["metrics"].update(data)
        elif event_type == StateEvent.CONFIG_CHANGED:
            self._state["config"].update(data)

    def _notify(self, event_type: StateEvent, data: Any):
        """Notify subscribers of state change"""
        for callback in self._subscribers[event_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

    def _record_change(self, event_type: StateEvent, data: Any):
        """Record state change in history"""
        change = StateChange(event_type=event_type, data=data)
        self._history.append(change)
        
        # Limit history size
        if len(self._history) > 1000:
            self._history = self._history[-1000:]