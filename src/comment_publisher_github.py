import os
import requests
import logging

def publish_comment(comment_obj, config):
    """
    Publishes a comment on a GitHub pull request including code context.
    
    Expects comment_obj to be a dictionary with the following keys:
      - "file": relative path of the file (e.g., "src/main.py")
      - "line": line number (exact line or range) of the change
      - "comment": feedback provided by the LLM
      - (optional) "context": code snippet context; if absent, it will be fetched automatically
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    if not repo or not pr_number:
        logging.error("Environment variables REPOSITORY_GITHUB and PR_NUMBER_GITHUB must be set.")
        return False

    file_info = comment_obj.get("file", "unknown file")
    line_info = comment_obj.get("line", "unknown line")
    feedback_text = comment_obj.get("comment", "")

    # Automatically fetch code context if not provided
    code_context = comment_obj.get("context", "")
    if not code_context:
        try:
            # Convert line_info to integer if necessary
            line_number = int(line_info)
            code_context = get_code_context(file_info, line_number, context_lines=3)
        except Exception as e:
            logging.error("Error retrieving context for file %s, line %s: %s", file_info, line_info, e)
            code_context = ""

    # Build the Markdown-formatted message
    body = f"**File:** `{file_info}`\n**Line:** {line_info}\n\n"
    body += f"**Feedback:**\n{feedback_text}\n\n"
    if code_context:
        body += "**Code Context:**\n"
        body += "```python\n"
        body += code_context
        body += "\n```\n"

    url = f"{config.GITHUB_API_URL}/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"body": body}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.info("Comment published successfully on PR #%s.", pr_number)
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Error publishing comment: %s", e)
        return False

def get_code_context(file_path, line_number, context_lines=3, ref=None):
    """
    Retrieves a code snippet from a given file around a specific line.
    
    Args:
      file_path (str): Relative file path (e.g., "src/main.py")
      line_number (int): Target line number (1-indexed)
      context_lines (int): Number of lines before and after to include
      ref (str, optional): Branch name or commit SHA; defaults to environment variables
    Returns:
      str: Code snippet including the target line and context
    Raises:
      Exception: If file retrieval fails
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    token = os.getenv("GITHUB_TOKEN")
    if not repo or not token:
        raise ValueError("Environment variables REPOSITORY_GITHUB and GITHUB_TOKEN must be set.")
    
    # Use provided ref or default environment variables
    if not ref:
        ref = os.getenv("GITHUB_HEAD_REF") or os.getenv("GITHUB_REF")
    
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.raw"
    }
    params = {}
    if ref:
        params["ref"] = ref

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Error retrieving file {file_path}: {response.status_code} - {response.text}")
    
    content = response.text
    lines = content.splitlines()
    index = line_number - 1  # Convert to 0-indexed
    start = max(0, index - context_lines)
    end = min(len(lines), index + context_lines + 1)
    snippet = "\n".join(lines[start:end])
    return snippet
