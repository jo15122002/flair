import os
import requests
import logging

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

def publish_review_with_suggestions(comments, config):
    """
    Creates a single GitHub Pull Request Review with:
      1. A summary overview in the review body
      2. Each suggestion as an inline comment under that review

    :param comments: List of dicts, each with keys:
                     - "file": path to the file
                     - "line": line number (int or numeric string)
                     - "comment": suggestion text
    :param config: Config object with GITHUB_API_URL and GITHUB_TOKEN
    :return: True if the review was posted successfully, False otherwise.
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    token = config.GITHUB_TOKEN

    if not repo or not pr_number or not token:
        logging.error("REPOSITORY_GITHUB, PR_NUMBER_GITHUB and GITHUB_TOKEN must be set.")
        return False

    # Build the review summary body
    total = len(comments)
    summary = (
        "## Pull Request Review Summary\n\n"
        f"I generated **{total}** suggestion{'s' if total != 1 else ''} in this review.\n\n"
        "### Suggestions Overview\n"
    )
    summary += "| # | File | Line | Suggestion |\n"
    summary += "| - | ---- | ---- | ---------- |\n"
    for idx, c in enumerate(comments, start=1):
        file = c.get("file", "unknown")
        line = c.get("line", "?")
        text = c.get("comment", "").replace("\n", " ")
        summary += f"| {idx} | `{file}` | {line} | {text} |\n"

    # Build inline comments array
    inline_comments = []
    for c in comments:
        try:
            line_number = int(c.get("line"))
        except (TypeError, ValueError):
            logging.warning("Skipping comment with invalid line: %s", c)
            continue
        inline_comments.append({
            "path": c.get("file"),
            "side": "RIGHT",
            "line": line_number,
            "body": c.get("comment", "")
        })

    payload = {
        "body": summary,
        "event": "COMMENT",
        "comments": inline_comments
    }

    url = f"{config.GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        logging.info("Posted PR review with %d inline comment(s) on #%s", len(inline_comments), pr_number)
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Failed to post PR review: %s", e)
        return False