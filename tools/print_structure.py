# tools/print_structure.py
import os
from pathlib import Path
from typing import Set

def print_directory_structure(
    startpath: str = '.',
    ignore_dirs: Set[str] = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv'},
    ignore_files: Set[str] = {'.gitignore', '.env', '*.pyc'},
    indent: str = '    '
) -> None:
    """
    Print the directory structure starting from startpath.
    
    Args:
        startpath: Root directory to start from
        ignore_dirs: Directories to ignore
        ignore_files: File patterns to ignore
        indent: Indentation string
    """
    # Convert startpath to absolute path
    startpath = os.path.abspath(startpath)
    
    # Print the root directory name
    print(f'\nProject Structure for: {os.path.basename(startpath)}')
    print('=' * 50)

    def should_ignore(path: str, patterns: Set[str]) -> bool:
        """Check if path matches any of the ignore patterns."""
        name = os.path.basename(path)
        return any(
            name == pattern or 
            (pattern.startswith('*') and name.endswith(pattern[1:]))
            for pattern in patterns
        )

    for root, dirs, files in os.walk(startpath):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(d, ignore_dirs)]
        
        # Calculate level for indentation
        level = root[len(startpath):].count(os.sep)
        
        # Print directory name
        indent_str = indent * level
        folder_name = os.path.basename(root)
        if level == 0:
            print('📁 .')
        else:
            print(f'{indent_str}📁 {folder_name}')
        
        # Print files
        file_indent = indent * (level + 1)
        for file in sorted(files):
            if not should_ignore(file, ignore_files):
                print(f'{file_indent}📄 {file}')

if __name__ == '__main__':
    # Get the project root directory (assuming this script is in tools/)
    project_root = str(Path(__file__).parent.parent)
    
    print_directory_structure(
        startpath=project_root,
        ignore_dirs={
            '.git', '__pycache__', '.pytest_cache',
            '.venv', 'venv', 'node_modules', '.idea'
        },
        ignore_files={
            '.gitignore', '.env', '*.pyc', '.DS_Store',
            '*.pyo', '*.pyd', '.Python', '*.so'
        }
    )