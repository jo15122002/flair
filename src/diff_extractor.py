import logging
import re
import subprocess
import requests
import os

def get_diff_from_pr():
    """
    Retrieves the diff directly via the GitHub API using the pull request diff URL.
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
    """
    Splits the diff into chunks of 'chunk_size' characters.
    """
    if not diff:
        return []
    return [diff[i:i+chunk_size] for i in range(0, len(diff), chunk_size)]

def filter_diff(diff, exclude_patterns=None):
    """
    Filters the diff to exclude entire file blocks whose paths contain any undesirable pattern.
    A file block (including its header) is removed if its file path contains any pattern in exclude_patterns.
    """
    if exclude_patterns is None:
        exclude_patterns = ['test', 'tests', 'spec']
    
    filtered_lines = []
    skip_file = False
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            # Determine file name from header line
            parts = line.split()
            if len(parts) >= 3:
                file_a = parts[2]  # expected format: "a/path/to/file"
                filename = file_a[2:] if file_a.startswith("a/") else file_a
                # If any pattern is found in filename, mark to skip this file block
                skip_file = any(pat.strip().lower() in filename.lower() for pat in exclude_patterns)
            else:
                skip_file = False
            # Only add the header if this block is not to be skipped
            if not skip_file:
                filtered_lines.append(line)
        else:
            if not skip_file:
                filtered_lines.append(line)
    return "\n".join(filtered_lines)

def split_diff_intelligent(diff, max_lines=1000):
    """
    Splits the diff into file blocks and subdivides blocks that exceed max_lines.
    Assumes each file diff block starts with "diff --git".
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
    Processes a unified diff by annotating it with the new file's line numbers.
    
    - For context lines (starting with ' ') and added lines (starting with '+'),
      prefixes the line with "Line <number>:" and increments the counter.
    - For removed lines (starting with '-'), annotates with "[REMOVED]" (without incrementing).
    - Hunk headers are preserved.
    
    Returns the annotated diff as a string.
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