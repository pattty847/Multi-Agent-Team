# start.py
import sys
import atexit
from src.config import SystemConfig
from src.executor import EnhancedDockerExecutor
from src.agents import TeamManager
from src.task_decomposition import decompose_and_execute

def cleanup(executor):
    """Ensure cleanup happens exactly once"""
    if hasattr(cleanup, 'done'):
        return
    try:
        executor.stop()
        print("\nCleaned up resources.")
    except Exception as e:
        print(f"\nError during cleanup: {str(e)}")
    finally:
        cleanup.done = True

def main():
    # Initialize configuration
    config = SystemConfig()
    executor = None
    
    try:
        # Create executor
        executor = EnhancedDockerExecutor(
            image=config.DOCKER_IMAGE,
            timeout=config.CODE_TIMEOUT,
            workspace=config.WORKING_DIR
        )
        
        # Register cleanup
        atexit.register(cleanup, executor)
        
        # Create team manager
        team_manager = TeamManager(config, executor)
        
        # Example complex task
        task = """Create a comprehensive analysis of recent AI developments:
        1. Research recent AI papers and breakthroughs
        2. Analyze their potential impact
        3. Create visualizations of key findings
        4. Implement code examples
        5. Ensure quality and accuracy
        """
        
        # Decompose and execute the task
        results = decompose_and_execute(task, config, team_manager)
        
        # Print results
        print("\nTask Completion Summary:")
        print("=" * 50)
        for task_id, result in results.items():
            print(f"\nTask {task_id}:")
            print("-" * 20)
            print(result)
        
    except KeyboardInterrupt:
        print("\nTerminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()