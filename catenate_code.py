#!/usr/bin/env python
import os
import argparse

def find_code_files(directory, extensions):
    """
    Recursively finds all files with the given extensions in the specified directory.

    Args:
    - directory (str): The directory to search in.
    - extensions (List[str]): List of file extensions to search for.

    Returns:
    - List[str]: A list of file paths relative to the project root.
    """
    code_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                relative_path = os.path.relpath(os.path.join(root, file), directory)
                code_files.append(relative_path)
    return code_files

def concatenate_files(files, project_root):
    """
    Concatenates the content of the files into a single string, 
    with each file's content preceded by a header with the file's relative path.

    Args:
    - files (List[str]): List of relative file paths to concatenate.
    - project_root (str): The root directory of the project.

    Returns:
    - str: The concatenated output as a single string.
    """
    output = []
    for file in files:
        header = f"\n\n$$NEWFILE$$ {file}\n\n"
        output.append(header)
        with open(os.path.join(project_root, file), 'r') as infile:
            output.append(infile.read())
            output.append("\n")  # Add a newline after each file's content
    return ''.join(output)

def main():
    parser = argparse.ArgumentParser(description="Recursively concatenate code files with specified extensions.")
    parser.add_argument('directory', type=str, help="The root directory to start searching from.")
    parser.add_argument('extensions', type=str, nargs='+', help="List of file extensions to search for (e.g., .py .js .html).")
    
    args = parser.parse_args()

    # Find all code files with the specified extensions
    code_files = find_code_files(args.directory, args.extensions)
    
    # Concatenate all files
    output = concatenate_files(code_files, args.directory)
    
    # Output to STDOUT
    print(output)

if __name__ == "__main__":
    main()
