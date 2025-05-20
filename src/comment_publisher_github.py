import os
import requests
import logging
import re

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
    Crée une seule Pull Request Review avec un résumé en body
    et des inline comments pour chaque suggestion dont on trouve
    la position dans le diff.
    """
    repo      = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    token     = config.GITHUB_TOKEN

    if not repo or not pr_number or not token:
        logging.error("REPOSITORY_GITHUB, PR_NUMBER_GITHUB and GITHUB_TOKEN must be set.")
        return False

    # Récupère le diff complet stocké plus tôt dans main.py
    diff = os.getenv("LLM_DIFF_CONTENT", "")

    # Build summary body
    total = len(comments)
    summary = (
        "## Pull Request Review Summary\n\n"
        f"I generated **{total}** suggestion{'s' if total != 1 else ''} in this review.\n\n"
        "### Suggestions Overview\n"
        "| # | File | Line | Suggestion |\n"
        "| - | ---- | ---- | ---------- |\n"
    )
    for idx, c in enumerate(comments, start=1):
        file = c.get("file","unknown")
        line = c.get("line","?")
        text = c.get("comment","").replace("\n"," ")
        summary += f"| {idx} | `{file}` | {line} | {text} |\n"

    # Build inline comments
    inline_comments = []
    for c in comments:
        path = c.get("file")
        try:
            line_number = int(c.get("line"))
            position = compute_diff_position(diff, path, line_number)
        except (ValueError, TypeError) as e:
            logging.warning(
                "Skipping inline comment for %s:%s — %s",
                path, c.get("line"), e
            )
            continue

        inline_comments.append({
            "path":     path,
            "position": position,
            "body":     c.get("comment","")
        })

    payload = {
        "body":    summary,
        "event":   "COMMENT",
        "comments": inline_comments
    }

    url = f"{config.GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/vnd.github.v3+json"
    }

    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        logging.info(
            "Posted PR review with %d inline comment(s) on #%s",
            len(inline_comments), pr_number
        )
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Failed to post PR review: %s", e)
        return False
    
def compute_diff_position(diff_text: str, file_path: str, target_line: int) -> int:
    """
    Pour le diff complet `diff_text`, trouve la position dans le hunk
    correspondant à `target_line` du fichier `file_path`.
    """
    in_target_file = False
    in_hunk = False
    position = 0
    current_new = None

    for line in diff_text.splitlines():
        # Début d'un nouveau fichier
        if line.startswith("diff --git"):
            in_target_file = (file_path in line)
            in_hunk = False
            continue

        if not in_target_file:
            continue

        # On ignore les headers de fichier
        if line.startswith("--- ") or line.startswith("+++ "):
            continue

        # Début d'un hunk : on extrait le numéro de départ
        if line.startswith("@@"):
            in_hunk = True
            position = 0
            m = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if not m:
                raise ValueError(f"Hunk header mal formé : {line}")
            current_new = int(m.group(1))
            continue

        if in_hunk:
            # Fin du bloc si on voit un nouveau diff
            if line.startswith("diff --git"):
                break

            # Chaque ligne de hunk (contexte, ajouté, supprimé) incrémente la position
            if line.startswith(" ") or line.startswith("+") or line.startswith("-"):
                position += 1

                # Pour les lignes nouvelles ou de contexte, on compare
                if line.startswith(" ") or line.startswith("+"):
                    # est-ce la ligne cible ?
                    if current_new == target_line:
                        return position
                    current_new += 1

    raise ValueError(f"Ligne {target_line} non trouvée dans le diff de {file_path}")