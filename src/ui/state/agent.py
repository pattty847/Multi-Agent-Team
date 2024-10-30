from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


@dataclass
class AgentState:
    """Represents the current state of an agent with enhanced type tracking"""
    name: str
    agent_type: str  # "Research", "Code", "Viz", "QA", "PM"
    role: str
    status: str
    tasks_completed: int
    memory_usage: float
    cpu_usage: float
    last_active: datetime
    position: Tuple[int, int] = (0, 0)
    current_task: Optional[str] = None
    specialization: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

    @property
    def display_name(self) -> str:
        """Returns a formatted display name including the agent type"""
        return f"{self.name} ({self.agent_type})"