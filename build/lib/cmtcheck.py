import argparse

import requests

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

import os

from pathlib import Path

import difflib

from cmtcheck_main import main as cmtcheck_main


def get_file_from_github(path, branch="main"):
    try:
        # Get the parent directory of the current script
        parent_dir = os.getcwd()
        
        # Open the Git repository
        try:
            repo = Repo(parent_dir)
        except NoSuchPathError:
            raise FileNotFoundError(f"The repository path '{parent_dir}' does not exist.")
        except InvalidGitRepositoryError:
            raise RuntimeError(f"The path '{parent_dir}' is not a valid Git repository.")
        
        # Attempt to read the file content from the branch
        try:
            git_file_content = repo.git.show(f"{branch}:{path}")
        except GitCommandError as e:
            error_message = str(e)
            if "Path '" in error_message and "' does not exist in" in error_message:
                raise FileNotFoundError(f"The file '{path}' does not exist in branch '{branch}'.")
            elif "fatal: invalid ref" in error_message or "unknown revision" in error_message:
                raise ValueError(f"The branch '{branch}' does not exist in the repository.")
            else:
                raise RuntimeError(f"Git error while accessing '{path}' in branch '{branch}': {e}")

        # Construct the local file path
        file_dir = os.path.join(parent_dir, path)
        return {'git_file_content': git_file_content, 'file_dir': file_dir}

    except Exception as e:
        # Raise the exception to propagate it properly
        raise e


def get_file_from_local(path):
    try:
        with open(path, "r") as file:
            local_file_content = file.read()
        return local_file_content
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{path}' was not found.")
    except PermissionError:
        raise PermissionError(f"Permission denied to read the file '{path}'.")
    except Exception as e:
        raise RuntimeError(f"Unexpected error while reading '{path}': {e}")
    

def hunke_generator(old_file, updated_file):
    diff = difflib.unified_diff(
    old_file,
    updated_file,
    lineterm=''  
    )
    return list(diff)  

def main():

    parser = argparse.ArgumentParser(description="Process some command-line arguments.")

    parser.add_argument("--path", type=str, help="Path to the file containing" \
    " the file name in the repository")

    parser.add_argument("--branch", type=str, default="main", help="Git branch name (default: main)")
    
    arguments = parser.parse_args()

    path = arguments.path

    brench = arguments.branch

    file_detailes = get_file_from_github(path, brench)

    current_git_file_content = file_detailes['git_file_content']

    target_file_path = file_detailes['file_dir']

    updated_file_content = get_file_from_local(target_file_path)

    code_diff = hunke_generator(
        current_git_file_content.splitlines(),
        updated_file_content.splitlines()
    )

    code_diff = "\n".join(code_diff)

    final_code = cmtcheck_main(initial_code=code_diff)

    print("\n✅ Final refined code:\n", final_code)
