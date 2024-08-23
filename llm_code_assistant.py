#!/usr/bin/env python
import os
import json
import argparse
import requests
from catenate_code import find_code_files, concatenate_files

def load_config(config_file):
    """Load configuration from a JSON file."""
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return json.load(file)
    return {}

def construct_prompt(code, user_query):
    """
    Construct the system and user prompts for the LLM.
    """
    system_prompt = "You are an assistant specialized in code analysis and modifications."
    user_prompt = f"{user_query}\n\nHere is every file in the codebase to consider, catenated together into one payload. Each file is seperated by a header of two newlines, a $$NEWFILE$$ token with the relative path and filename, and then two more newlines:\n{code}"
    
    return system_prompt, user_prompt

def send_request(api_url, api_key, model, system_prompt, user_prompt):
    """
    Send the prompt to the LLM and return the response.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    
    # Check for errors and print more detailed error information
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Error while communicating with the LLM: {err}")
        print("Response:", response.text)  # Print out the response for more details
        return None
    
    return response.json()

def save_diffs(diffs, output_dir):
    """
    Save the diffs to files in the specified output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    for diff in diffs:
        # Extract the file path and create a sensible name for the diff file
        file_path = diff.get("file_path", "unknown_file")
        summary = diff.get("summary", "changes").replace(" ", "_")[:50]
        diff_filename = f"{os.path.basename(file_path)}_{summary}.diff"
        diff_filepath = os.path.join(output_dir, diff_filename)
        
        with open(diff_filepath, 'w') as file:
            file.write(diff.get("diff_content", ""))

def main():
    parser = argparse.ArgumentParser(description="Automate code analysis and changes using LLMs.")
    parser.add_argument('-d', '--directory', type=str, required=False, help="The root directory of the project.")
    parser.add_argument('-e', '--extensions', type=str, required=False, nargs='+', help="File extensions to look for (e.g., .py .js .html).")
    parser.add_argument('-q', '--query', type=str, required=False, help="The query to ask the LLM about the code.")
    
    # Optional arguments
    parser.add_argument('-c', '--config', type=str, default="llm_config.json", help="Path to a JSON configuration file.")
    parser.add_argument('-u', '--api_url', type=str, help="API endpoint URL.")
    parser.add_argument('-k', '--api_key', type=str, help="API key for the LLM service.")
    parser.add_argument('-m', '--model', type=str, help="LLM model to use.")
    parser.add_argument('-o', '--output_dir', type=str, help="Directory to save the diff files.")
    
    args = parser.parse_args()

    # Load configuration from JSON file if it exists
    config = load_config(args.config)
    
    # Overwrite config values with command-line arguments if provided
    api_url = args.api_url or config.get("api_url", "https://api.openai.com/v1/chat/completions")
    api_key = args.api_key or config.get("api_key")
    model = args.model or config.get("model", "gpt-4")
    output_dir = args.output_dir or config.get("output_dir", "./diffs")
    
    # Directory, extensions, and query should be sourced from args or config
    directory = args.directory or config.get("directory")
    extensions = args.extensions or config.get("extensions")
    query = args.query or config.get("query")
    
    if not api_key:
        raise ValueError("API key is required. Provide it via command-line argument or in the configuration file.")
    
    if not directory:
        raise ValueError("Directory is required. Provide it via command-line argument or in the configuration file.")
    
    if not extensions:
        raise ValueError("File extensions are required. Provide them via command-line argument or in the configuration file.")
    
    if not query:
        raise ValueError("Query is required. Provide it via command-line argument or in the configuration file.")

    # Get code files and concatenate them
    code_files = find_code_files(directory, extensions)
    code = concatenate_files(code_files, directory)
    
    # Construct the prompt
    system_prompt, user_prompt = construct_prompt(code, query)
    
    # Send the prompt to the LLM
    response = send_request(api_url, api_key, model, system_prompt, user_prompt)
    if not response:
        return
    
    # Handle the response (assuming the LLM provides a structured response)
    if "choices" in response and len(response["choices"]) > 0:
        llm_output = response["choices"][0]["message"]["content"]
        print(f"LLM Response:\n{llm_output}")
        
        # Example of detecting diffs (depends on the format returned by the LLM)
        diffs = extract_diffs(llm_output)
        if diffs:
            save_diffs(diffs, output_dir)
            print(f"Diff files saved to {output_dir}.")
    else:
        print("No valid response from the LLM.")

def extract_diffs(llm_output):
    """
    Placeholder function to extract diffs from the LLM output.
    This needs to be customized based on how the LLM structures its output.
    """
    # This function should parse the LLM output and return a list of diffs
    # Each diff should be a dictionary with at least "file_path" and "diff_content"
    # Add "summary" if you want to generate a short description for the diff file name
    diffs = []
    # Example structure:
    # diffs = [{"file_path": "path/to/file.py", "diff_content": "diff --git ...", "summary": "Fixed bug in X"}]
    return diffs

if __name__ == "__main__":
    main()
