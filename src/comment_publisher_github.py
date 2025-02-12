import os
import requests
import logging

def publish_comment(comment_obj, config):
    """
    Publishes a comment on a GitHub pull request using the LLM feedback object.
    
    Expects comment_obj to be a dictionary with the following keys:
      - "file": the filename (e.g. "src/main.py")
      - "line": the line number or range (e.g. 42 or "40-45")
      - "comment": the feedback text for that section
      
    The function constructs a message that includes this information and
    posts it as a comment on the pull request.
    """
    repo = os.getenv("GITHUB_REPOSITORY")  # Format: "owner/repo"
    pr_number = os.getenv("PR_NUMBER")  # The pull request number as a string
    if not repo or not pr_number:
        logging.error("Environment variables GITHUB_REPOSITORY and PR_NUMBER must be set.")
        return False

    # Construire le corps du message en intégrant les informations du feedback
    file_info = comment_obj.get("file", "unknown file")
    line_info = comment_obj.get("line", "unknown line")
    feedback_text = comment_obj.get("comment", "")
    
    # On peut formater le message de façon claire pour le lecteur
    body = f"**File:** `{file_info}`\n**Line:** {line_info}\n\n{feedback_text}"

    # URL de l'API pour poster un commentaire sur la PR (endpoint issues)
    url = f"{config.GITHUB_API_URL}/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {config.TOKEN_GITHUB}",
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
