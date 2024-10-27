import signal
from contextlib import contextmanager
from autogen.coding import DockerCommandLineCodeExecutor
import tempfile
import os

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class EnhancedDockerExecutor(DockerCommandLineCodeExecutor):
    def __init__(self, image: str, timeout: int = 30, workspace: str = None):
        self.workspace = workspace or tempfile.mkdtemp()
        os.makedirs(self.workspace, exist_ok=True)
        super().__init__(
            image=image,
            timeout=timeout,
            work_dir=self.workspace
        )
    
    def execute_with_error_handling(self, code: str) -> str:
        try:
            with time_limit(self.timeout):
                result = self.execute(code)
                return result
        except TimeoutException:
            return "Execution timed out!"
        except Exception as e:
            return f"Error during execution: {str(e)}"