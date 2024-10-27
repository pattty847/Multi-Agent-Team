import logging
from typing import Optional
import signal
import logging
from typing import Optional

from src.agents import EnhancedUserProxy
from src.core.config import SystemConfig
from src.core.executor import EnhancedDockerExecutor

class GracefulExitHandler:
    def __init__(self):
        self.exit_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.exit_now = True
        print("\nReceived exit signal. Cleaning up...")
        
# Main application

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class MultiAgentSystem:
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        self.exit_handler = GracefulExitHandler()
        self.executor = EnhancedDockerExecutor(
            image=self.config.DOCKER_IMAGE,
            timeout=self.config.CODE_TIMEOUT,
            workspace=self.config.WORKING_DIR
        )
        self.assistant = EnhancedAssistantAgent("assistant", self.config)
        self.user_proxy = EnhancedUserProxy("user_proxy", self.executor)
        setup_logging()

    def run_task(self, task_message: str, save_history: bool = True) -> None:
        try:
            self.user_proxy.initiate_chat(
                self.assistant,
                message=task_message
            )
            if save_history:
                self.user_proxy.save_conversation("conversation_history.txt")
        except KeyboardInterrupt:
            print("\nGracefully shutting down...")
        except Exception as e:
            logging.error(f"Error during task execution: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            self.executor.stop()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
