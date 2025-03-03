import logging
import re
import subprocess

import requests


def get_diff_from_pr():
    """
    Retrieves the diff via the GitHub API.
    Requires REPOSITORY_GITHUB, PR_NUMBER_GITHUB, and GITHUB_TOKEN to be set.
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    token = os.getenv("GITHUB_TOKEN")
    
    if not repo:
        logging.error("Environment variable REPOSITORY_GITHUB must be set.")
        return None
    if not pr_number:
        logging.error("Environment variable PR_NUMBER_GITHUB must be set.")
        return None
    if not token:
        logging.error("Environment variable GITHUB_TOKEN must be set.")
        return None

    diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    try:
        response = requests.get(diff_url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error("Error retrieving diff via GitHub API: %s", e)
        return None

def split_diff(diff, chunk_size):
    """Splits the diff into chunks of 'chunk_size' characters."""
    if not diff:
        return []
    return [diff[i:i+chunk_size] for i in range(0, len(diff), chunk_size)]

def filter_diff(diff, exclude_patterns=None):
    """
    Filters the diff to exclude file blocks whose paths contain any unwanted pattern.
    """
    if exclude_patterns is None:
        exclude_patterns = ['test', 'tests', 'spec']
    
    filtered_lines = []
    skip_file = False
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                file_a = parts[2]  # e.g. "a/path/to/file"
                filename = file_a[2:] if file_a.startswith("a/") else file_a
                skip_file = any(pat.strip().lower() in filename.lower() for pat in exclude_patterns)
            else:
                skip_file = False
            if not skip_file:
                filtered_lines.append(line)
        else:
            if not skip_file:
                filtered_lines.append(line)
    return "\n".join(filtered_lines)

def split_diff_intelligent(diff, max_lines=1000):
    """
    Splits the diff into file blocks and further subdivides blocks that exceed max_lines.
    """
    blocks = re.split(r'(?=^diff --git)', diff, flags=re.MULTILINE)
    chunks = []
    for block in blocks:
        if not block.strip():
            continue
        lines = block.splitlines()
        if len(lines) <= max_lines:
            chunks.append(block)
        else:
            for i in range(0, len(lines), max_lines):
                sub_block = "\n".join(lines[i:i+max_lines])
                chunks.append(sub_block)
    return chunks

def preprocess_diff_with_line_numbers(diff):
    """
    Annotates the diff with new file line numbers.
    Context and added lines are prefixed with "Line <number>:".
    Removed lines are marked with "[REMOVED]".
    """
    lines = diff.splitlines()
    processed_lines = []
    new_line_number = None
    hunk_header_pattern = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')

    for line in lines:
        if line.startswith('@@'):
            match = hunk_header_pattern.match(line)
            if match:
                new_line_number = int(match.group(1))
            processed_lines.append(line)
        elif new_line_number is not None:
            if line.startswith(' '):
                annotated_line = f"Line {new_line_number}: {line[1:]}"
                processed_lines.append(annotated_line)
                new_line_number += 1
            elif line.startswith('+'):
                annotated_line = f"Line {new_line_number}: {line[1:]}"
                processed_lines.append(annotated_line)
                new_line_number += 1
            elif line.startswith('-'):
                annotated_line = f"[REMOVED] {line[1:]}"
                processed_lines.append(annotated_line)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return "\n".join(processed_lines)

def extract_file_paths(diff):
    """
    Extracts a set of file paths from the diff.
    Looks for lines starting with "diff --git" and extracts the path from the "a/" side.
    """
    file_paths = set()
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                file_a = parts[2]
                file_path = file_a[2:] if file_a.startswith("a/") else file_a
                file_paths.add(file_path)
    return file_paths

def get_full_file_content(file_path):
    """
    Retrieves the full content of the specified file using the GitHub API.
    Requires REPOSITORY_GITHUB and GITHUB_TOKEN to be set.
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    token = os.getenv("GITHUB_TOKEN")
    if not repo or not token:
        raise ValueError("Environment variables REPOSITORY_GITHUB and GITHUB_TOKEN must be set.")
    
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.raw"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error retrieving file {file_path}: {response.status_code} - {response.text}")
    return response.text
