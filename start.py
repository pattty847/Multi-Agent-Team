# start.py
import sys
import atexit
from src.config import SystemConfig
from src.executor import EnhancedDockerExecutor
from src.team_task import GroupTaskManager

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

def print_result_summary(result: dict):
    """Print a formatted summary of the task execution"""
    print("\nTask Execution Summary:")
    print("=" * 50)
    
    if "error" in result:
        print(f"\n❌ Task Failed:")
        print(f"Error: {result['error']}")
    else:
        print("\n✅ Task Completed")
        print(f"\nParticipants:")
        for participant in result['participants']:
            print(f"- {participant}")
        
        if result.get('chat_history'):
            print("\nKey Discussion Points:")
            for msg in result['chat_history'][-3:]:  # Show last 3 messages
                if isinstance(msg, dict) and 'content' in msg:
                    print(f"\n- {msg['content'][:100]}...")

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
        
        # Create task manager
        task_manager = GroupTaskManager(config, executor)
        
        # Example task that requires multiple agents
        task = """Research and implement a visualization of recent AI breakthroughs.
        1. Research recent AI papers
        2. Create visualizations of key findings
        3. Implement interactive dashboard
        4. Ensure code quality and documentation"""
        
        # Required agents for this task
        required_agents = ["research", "viz", "code", "qa", "pm"]
        
        # Execute the task
        result = task_manager.execute_task(task, required_agents)
        
        # Print summary
        print_result_summary(result)
        
    except KeyboardInterrupt:
        print("\nTerminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()