import os
import subprocess
import logging
import requests

def get_diff(config):
    """
    Extrait le diff entre la branche cible et la branche source.
    Pour GitHub Actions, on utilise GITHUB_HEAD_REF (branche source)
    et GITHUB_BASE_REF (branche cible).
    """
    # Récupérer les branches à partir des variables d'environnement
    source_branch = os.getenv("GITHUB_HEAD_REF")
    target_branch = os.getenv("GITHUB_BASE_REF")
    
    if not source_branch or not target_branch:
        logging.error("Les variables d'environnement GITHUB_HEAD_REF et GITHUB_BASE_REF doivent être définies.")
        return None

    try:
        # S'assurer que la branche cible est à jour (fetch)
        subprocess.run(["git", "fetch", "origin", target_branch], check=True)
        
        # Utiliser la notation à trois points pour obtenir le diff entre la branche cible et la source
        result = subprocess.run(
            ["git", "diff", f"origin/{target_branch}...", source_branch],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        diff = result.stdout
        return diff
    except subprocess.CalledProcessError as e:
        logging.error("Erreur lors de l'extraction du diff: %s", e)
        return None
    
def get_diff_from_pr():
    """
    Récupère le diff directement via l'API GitHub en utilisant l'URL de diff de la pull request.
    """
    repo = os.getenv("GITHUB_REPOSITORY")  # Format "owner/repo"
    pr_number = os.getenv("GITHUB_PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    
    if not repo or not pr_number or not token:
        logging.error("Les variables GITHUB_REPOSITORY, GITHUB_PR_NUMBER et GITHUB_TOKEN doivent être définies.")
        return None

    # Construire l'URL pour récupérer le diff
    diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"  # Spécifie le format diff
    }
    
    try:
        response = requests.get(diff_url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de la récupération du diff via l'API GitHub : %s", e)
        return None

def split_diff(diff, chunk_size):
    """
    Découpe le diff en plusieurs parties de taille 'chunk_size'
    si le diff est trop volumineux pour être traité en une seule fois.
    """
    if not diff:
        return []
    return [diff[i:i+chunk_size] for i in range(0, len(diff), chunk_size)]
