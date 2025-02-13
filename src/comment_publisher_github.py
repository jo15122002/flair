import os
import requests
import logging

def publish_comment(comment_obj, config):
    """
    Publie un commentaire sur une pull request GitHub en incluant le contexte du code.
    
    Expects comment_obj to be a dictionary with keys:
      - "file": chemin du fichier (ex: "src/main.py")
      - "line": numéro de ligne concernée
      - "comment": feedback du LLM
      - (optionnel) "context": si fourni, il sera remplacé par le contexte récupéré automatiquement
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    if not repo or not pr_number:
        logging.error("Les variables d'environnement REPOSITORY_GITHUB et PR_NUMBER_GITHUB doivent être définies.")
        return False

    file_info = comment_obj.get("file", "unknown file")
    line_info = comment_obj.get("line", "unknown line")
    feedback_text = comment_obj.get("comment", "")

    # Récupération automatique du contexte si non fourni
    code_context = comment_obj.get("context", "")
    if not code_context:
        try:
            # Convertir line_info en int si nécessaire
            line_number = int(line_info)
            code_context = get_code_context(file_info, line_number, context_lines=3)
        except Exception as e:
            logging.error("Erreur lors de la récupération du contexte pour le fichier %s, ligne %s: %s", file_info, line_info, e)
            code_context = ""

    # Construction du message formaté en Markdown
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
        logging.info("Commentaire publié avec succès sur la PR #%s.", pr_number)
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de la publication du commentaire: %s", e)
        return False

    
def get_code_context(file_path, line_number, context_lines=3, ref=None):
    """
    Récupère un extrait du code pour un fichier donné, autour d'une ligne spécifique.
    
    Args:
      file_path (str): chemin relatif du fichier (ex: "src/main.py")
      line_number (int): numéro de ligne concernée (1-indexé)
      context_lines (int): nombre de lignes avant et après à inclure
      ref (str, optionnel): nom de la branche ou SHA du commit. Si None, on utilise GITHUB_HEAD_REF ou GITHUB_REF.
      
    Returns:
      str: extrait de code contenant la ligne concernée plus context_lines lignes avant et après.
      
    Raises:
      Exception: en cas d'erreur lors de la récupération du fichier.
    """
    repo = os.getenv("REPOSITORY_GITHUB")  # Doit être au format "owner/repo"
    token = os.getenv("GITHUB_TOKEN")
    if not repo or not token:
        raise ValueError("Les variables d'environnement REPOSITORY_GITHUB et GITHUB_TOKEN doivent être définies.")
    
    # Utilise le ref spécifié, ou celui défini par défaut dans l'environnement
    if not ref:
        ref = os.getenv("GITHUB_HEAD_REF") or os.getenv("GITHUB_REF")
    
    # Construire l'URL de l'API GitHub pour récupérer le contenu du fichier.
    # On utilise un header pour demander le contenu brut.
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.raw"  # Pour obtenir le contenu brut
    }
    params = {}
    if ref:
        params["ref"] = ref

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Erreur lors de la récupération du fichier {file_path}: {response.status_code} - {response.text}")
    
    # Le contenu du fichier est dans response.text (pas de décodage base64 grâce à 'raw')
    content = response.text
    lines = content.splitlines()
    total_lines = len(lines)
    
    # Convertir le numéro de ligne en index (0-indexé)
    index = line_number - 1
    start = max(0, index - context_lines)
    end = min(total_lines, index + context_lines + 1)
    snippet = "\n".join(lines[start:end])
    return snippet
