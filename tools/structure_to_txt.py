import os
import fnmatch

def load_gitignore_patterns(gitignore_path='.gitignore'):
    """Load patterns from a .gitignore file."""
    with open(gitignore_path, 'r') as file:
        patterns = [line.strip() for line in file if line.strip() and not line.startswith('#')]
    return patterns

def is_ignored(path, patterns):
    """Check if a path matches any of the ignore patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False

def print_directory_structure(root_dir='.', gitignore_path='.gitignore'):
    """Print the directory structure, excluding files in .gitignore."""
    patterns = load_gitignore_patterns(gitignore_path)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter out ignored directories
        dirnames[:] = [d for d in dirnames if not is_ignored(os.path.join(dirpath, d), patterns)]
        # Filter out ignored files
        filenames = [f for f in filenames if not is_ignored(os.path.join(dirpath, f), patterns)]
        
        # Print the directory path
        print(f'{dirpath}/')
        # Print the filenames
        for filename in filenames:
            print(f'  {filename}')

# Example usage
print_directory_structure()