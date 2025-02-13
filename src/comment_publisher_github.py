import os
import requests
import logging

def publish_comment(comment_obj, config):
    """
    Publishes a comment on a GitHub pull request using the LLM feedback object.

    Expects comment_obj to be a dictionary with the following keys:
      - "file": the filename (e.g. "src/main.py")
      - "line": the line number or range (e.g. 42 or "40-45")
      - "comment": the feedback text for that section.
      - "context": (optional) a code snippet containing the relevant code along with 2-3 lines before and after.

    The function constructs a formatted markdown message that includes:
      - The file and line information.
      - The feedback provided by the LLM.
      - The code context in a syntax-highlighted block (if provided).
    """
    repo = os.getenv("GITHUB_REPOSITORY")  # Expected format: "owner/repo"
    pr_number = os.getenv("GITHUB_PR_NUMBER")
    if not repo or not pr_number:
        logging.error("Environment variables GITHUB_REPOSITORY and GITHUB_PR_NUMBER must be set.")
        return False

    file_info = comment_obj.get("file", "unknown file")
    line_info = comment_obj.get("line", "unknown line")
    feedback_text = comment_obj.get("comment", "")
    code_context = comment_obj.get("context", "")

    # Construire le corps du message avec une mise en forme markdown
    body = f"**File:** `{file_info}`\n**Line:** {line_info}\n\n"
    body += f"**Feedback:**\n{feedback_text}\n\n"
    
    # Ajout du contexte de code si fourni
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
