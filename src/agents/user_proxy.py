# src/agents/user_proxy.py
from typing import Optional, Dict
from autogen import UserProxyAgent
from src.config.agent_config import SystemConfig

class EnhancedUserProxy(UserProxyAgent):
    """Enhanced user proxy with better termination handling and history"""
    def __init__(self, name: str, executor, human_input_mode: str = "TERMINATE"):
        super().__init__(
            name=name,
            code_execution_config={"executor": executor},
            human_input_mode=human_input_mode,
            is_termination_msg=self._is_termination_msg
        )
        self.conversation_history = []
        
    def _is_termination_msg(self, msg: Dict) -> bool:
        """Check if message indicates task completion"""
        if not msg.get("content"):
            return False
            
        content = msg["content"].upper()
        return any(phrase in content for phrase in [
            "TERMINATE",
            "TASK_COMPLETED",
            "TASK TERMINATED BY USER"
        ])

    def generate_reply(self, messages: list, sender: Optional[object] = None, **kwargs):
        """Generate reply with history tracking"""
        try:
            reply = super().generate_reply(messages, sender, **kwargs)
            
            # Store in history if it's not a termination message
            if not self._is_termination_msg({"content": reply}):
                self.conversation_history.append({
                    "sender": sender.name if sender else "system",
                    "message": messages[-1]["content"],
                    "reply": reply
                })
            return reply
            
        except Exception as e:
            print(f"\nError during reply generation: {str(e)}")
            return f"Error occurred: {str(e)}"