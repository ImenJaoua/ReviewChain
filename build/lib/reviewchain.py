import argparse

import requests

from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

import os

from pathlib import Path

import difflib

import re

from reviewchain_main import main as cmtcheck_main

import difflib

class DiffParser:
    def __init__(self):
        self.files = []
    
    def parse_diff(self, diff_text: str, default_filename: str = "output.txt") -> list[dict]:
        """Parse a unified diff and extract the resulting code files."""
        lines = diff_text.split('\n')
        files = []
        current_file = None
        in_hunk = False
        
        print(f"DEBUG: Total lines in diff: {len(lines)}")
        
        for i, line in enumerate(lines):
            # Standard diff header: diff --git a/file b/file
            if line.startswith('diff --git'):
                if current_file and (current_file.get('name') or current_file.get('content')):
                    if not current_file.get('name'):
                        current_file['name'] = default_filename
                    print(f"DEBUG: Adding file '{current_file['name']}' with {len(current_file['content'])} lines")
                    files.append(current_file)
                print(f"DEBUG: Found diff header at line {i}")
                current_file = {
                    'name': '',
                    'content': [],
                    'is_new': False,
                    'is_deleted': False
                }
                in_hunk = False
                continue
            
            # New file mode
            if line.startswith('new file mode'):
                if not current_file:
                    current_file = {'name': '', 'content': [], 'is_new': False, 'is_deleted': False}
                current_file['is_new'] = True
                print(f"DEBUG: Marked as new file")
                continue
            
            # Deleted file mode
            if line.startswith('deleted file mode'):
                if not current_file:
                    current_file = {'name': '', 'content': [], 'is_new': False, 'is_deleted': False}
                current_file['is_deleted'] = True
                print(f"DEBUG: Marked as deleted file")
                continue
            
            # +++ b/filename or just +++ filename
            if line.startswith('+++'):
                if not current_file:
                    current_file = {'name': '', 'content': [], 'is_new': False, 'is_deleted': False}
                
                # Extract filename if present
                if line.startswith('+++ b/'):
                    current_file['name'] = line[6:].strip()
                elif len(line) > 4:
                    current_file['name'] = line[4:].strip()
                
                print(f"DEBUG: Set filename to '{current_file['name']}'")
                continue
            
            # --- a/filename or just --- filename
            if line.startswith('---'):
                if not current_file:
                    current_file = {'name': '', 'content': [], 'is_new': False, 'is_deleted': False}
                
                # Extract filename if present and not already set
                if not current_file.get('name'):
                    if line.startswith('--- a/'):
                        current_file['name'] = line[6:].strip()
                    elif len(line) > 4:
                        current_file['name'] = line[4:].strip()
                    print(f"DEBUG: Set filename from --- to '{current_file['name']}'")
                continue
            
            # Hunk header: @@ -start,count +start,count @@
            if line.startswith('@@'):
                if not current_file:
                    current_file = {'name': '', 'content': [], 'is_new': False, 'is_deleted': False}
                in_hunk = True
                print(f"DEBUG: Found hunk header at line {i}")
                continue
            
            # Content lines (only process if we're in a hunk)
            if in_hunk and current_file:
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line
                    current_file['content'].append(line[1:])
                elif line.startswith('-') and not line.startswith('---'):
                    # Deleted line - skip for new file generation
                    continue
                elif line.startswith(' '):
                    # Context line
                    current_file['content'].append(line[1:])
                else:
                    # Empty line or line without prefix
                    current_file['content'].append(line)
        
        # Add the last file
        if current_file and (current_file.get('name') or current_file.get('content')):
            if not current_file.get('name'):
                current_file['name'] = default_filename
            print(f"DEBUG: Adding last file '{current_file['name']}' with {len(current_file['content'])} lines")
            files.append(current_file)
        
        print(f"DEBUG: Total files parsed: {len(files)}")
        
        # Filter out deleted files
        filtered = [f for f in files if not f['is_deleted']]
        print(f"DEBUG: Files after filtering deleted: {len(filtered)}")
        return filtered
    
    def convert_diff_to_code(self, diff_text: str, default_filename: str = "output.txt") -> dict[str, str]:
        """Convert diff to a dictionary of filename -> code content."""
        files = self.parse_diff(diff_text, default_filename)
        
        if not files:
            print("WARNING: No files parsed from diff")
        
        result = {}
        
        for file in files:
            filename = file['name']
            content = '\n'.join(file['content'])
            result[filename] = content
            print(f"DEBUG: Converted file '{filename}' - {len(content)} characters")
        
        return result


class ColorFormatter:
    """Utility class for adding ANSI color codes and formatting to text."""
    
    # ANSI color codes
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def colorize(text, color_code):
        """Apply a color code to text and reset afterwards."""
        return f"{color_code}{text}{ColorFormatter.RESET}"
    
    @staticmethod
    def red(text):
        """Make text red."""
        return ColorFormatter.colorize(text, ColorFormatter.RED)
    
    @staticmethod
    def green(text):
        """Make text green."""
        return ColorFormatter.colorize(text, ColorFormatter.GREEN)
    
    @staticmethod
    def cyan(text):
        """Make text cyan."""
        return ColorFormatter.colorize(text, ColorFormatter.CYAN)
    
    @staticmethod
    def yellow(text):
        """Make text yellow."""
        return ColorFormatter.colorize(text, ColorFormatter.YELLOW)
    
    @staticmethod
    def blue(text):
        """Make text blue."""
        return ColorFormatter.colorize(text, ColorFormatter.BLUE)
    
    @staticmethod
    def magenta(text):
        """Make text magenta."""
        return ColorFormatter.colorize(text, ColorFormatter.MAGENTA)
    
    @staticmethod
    def bold(text):
        """Make text bold."""
        return ColorFormatter.colorize(text, ColorFormatter.BOLD)
    
    @staticmethod
    def underline(text):
        """Make text underlined."""
        return ColorFormatter.colorize(text, ColorFormatter.UNDERLINE)
    
    @staticmethod
    def bold_cyan(text):
        """Make text bold and cyan."""
        return f"{ColorFormatter.BOLD}{ColorFormatter.CYAN}{text}{ColorFormatter.RESET}"


def display_github_style_diff(diff_text, filename):
    """
    Display the diff in GitHub-style format with color-coded additions and deletions.
    This function handles the specific hunk diff display logic.
    """
    lines = diff_text.split('\n')
    
    print("\n" + "=" * 80)
    print(ColorFormatter.bold_cyan(f"📝 Detected Changes in: {filename}"))
    print("=" * 80 + "\n")
    
    additions = 0
    deletions = 0
    
    for line in lines:
        if line.startswith('@@'):
            # Hunk header - display in cyan
            print(ColorFormatter.cyan(line))
        elif line.startswith('+') and not line.startswith('+++'):
            # Addition - display in green
            print(ColorFormatter.green(line))
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            # Deletion - display in red
            print(ColorFormatter.red(line))
            deletions += 1
        elif line.startswith('+++') or line.startswith('---'):
            # File headers - display in bold
            print(ColorFormatter.bold(line))
        else:
            # Context lines
            print(line)
    
    # Summary
    print("\n" + "-" * 80)
    summary = f"{ColorFormatter.bold('Summary:')} {ColorFormatter.green(f'+{additions} additions')}, {ColorFormatter.red(f'-{deletions} deletions')}"
    print(summary)
    print("-" * 80 + "\n")


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

def apply_unified_diff(original_content, diff_text):
    """
    Apply a unified diff patch to the original content.
    If no correlation exists between original_content and diff_text,
    just replace the original_content with diff_text.
    """
    original_lines = original_content.splitlines(keepends=True)
    
    # Parse the diff to extract changes
    diff_lines = diff_text.splitlines()
    
    # Find the hunk header (@@)
    hunk_pattern = r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@'
    
    # Check if diff_text contains any hunk headers (valid unified diff)
    has_hunks = any(re.match(hunk_pattern, line) for line in diff_lines)
    
    # If no hunks found, there's no correlation - just replace content
    if not has_hunks:
        return diff_text if diff_text.endswith('\n') or not diff_text else diff_text + '\n'
    
    result_lines = original_lines.copy()
    offset = 0  # Track line number offset as we make changes
    
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]
        
        # Look for hunk headers
        match = re.match(hunk_pattern, line)
        if match:
            old_start = int(match.group(1))
            old_count = int(match.group(2))
            new_start = int(match.group(3))
            new_count = int(match.group(4))
            
            # Adjust for 0-based indexing
            old_start_idx = old_start - 1 + offset
            
            # Check if the hunk references are out of bounds (no correlation)
            if old_start_idx < 0 or old_start_idx >= len(result_lines):
                # No valid correlation, replace entire content
                return diff_text if diff_text.endswith('\n') or not diff_text else diff_text + '\n'
            
            # Collect the new lines from this hunk
            new_lines = []
            i += 1
            
            while i < len(diff_lines):
                hunk_line = diff_lines[i]
                
                # Stop at next hunk or end
                if hunk_line.startswith('@@'):
                    i -= 1
                    break
                
                # Lines starting with '+' are additions
                if hunk_line.startswith('+'):
                    new_lines.append(hunk_line[1:] + '\n')
                # Lines starting with ' ' (space) are context - keep them
                elif hunk_line.startswith(' '):
                    new_lines.append(hunk_line[1:] + '\n')
                # Lines starting with '-' are deletions - skip them
                elif hunk_line.startswith('-'):
                    pass
                
                i += 1
            
            # Replace the old lines with new lines
            result_lines = (
                result_lines[:old_start_idx] +
                new_lines +
                result_lines[old_start_idx + old_count:]
            )
            
            # Update offset
            offset += len(new_lines) - old_count
        
        i += 1
    
    return ''.join(result_lines)


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

    display_github_style_diff(code_diff, path)

    print("\n" + "=" * 80)
    print(ColorFormatter.bold_cyan(f"🚀 Review Chain Pipeline"))
    print("=" * 80 + "\n")

    final_code = cmtcheck_main(initial_code=code_diff)    

    parser = DiffParser()

    files = parser.convert_diff_to_code(final_code)

    # Print results
    for filename, content in files.items():
        print("\n" + "=" * 80)
        print(ColorFormatter.bold_cyan(f"⚙️  Proposed Refinement"))
        print("=" * 80 + "\n")
        print(content)
        print("\n")


    print("\n" + "=" * 80)
    print(ColorFormatter.bold_cyan(f"👤 User Decision"))
    print("=" * 80 + "\n")
    
    # User confirmation step
    while True:
        user_input = input("\nDo you want to apply these changes to the file? (y/n): ").strip().lower()
        if user_input == 'y':
            print("\nApplying changes...")
            
            # Apply the unified diff to the current file content
            final_content = apply_unified_diff(updated_file_content, final_code)
            
            # Write the modified content back to the target file
            with open(target_file_path, 'w') as f:
                f.write(final_content)
            print(f"✅ Updated: {target_file_path}")
            break
        elif user_input == 'n':
            print("\n❌ Changes cancelled. File not updated.")
            break
        else:
            print("Invalid input. Please enter 'y' for yes or 'n' for no.")