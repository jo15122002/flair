import os
import subprocess
import logging
import requests
import re

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
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    token = os.getenv("GITHUB_TOKEN")
    
    if not repo :
        logging.error("La variable d'environnement REPOSITORY_GITHUB doit être définie.")
        return None
    if not pr_number:
        logging.error("La variable d'environnement PR_NUMBER_GITHUB doit être définie.")
        return None
    if not token:
        logging.error("La variable d'environnement GITHUB_TOKEN doit être définie.")
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

def filter_diff(diff, exclude_patterns=None):
    def filter_diff(diff, exclude_patterns=None):
        """
        Filtre le diff pour exclure les fichiers dont le chemin contient un motif
        indésirable.
        Si aucun pattern n'est fourni, on utilise une liste par défaut.
        """
    if exclude_patterns is None:
        exclude_patterns = ['test', 'tests', 'spec']
    
    filtered_lines = []
    skip_file = False
    for line in diff.splitlines():
        # Détecte le début d'un bloc de fichier
        if line.startswith("diff --git"):
            # Exemple de ligne : "diff --git a/src/main.py b/src/main.py"
            parts = line.split()
            if len(parts) >= 3:
                file_a = parts[2]  # attend "a/chemin/du/fichier"
                filename = file_a[2:] if file_a.startswith("a/") else file_a
                # Vérifie si le nom de fichier contient un des motifs d'exclusion
                skip_file = any(pat.strip().lower() in filename.lower() for pat in exclude_patterns)
            filtered_lines.append(line)
        else:
            if not skip_file:
                filtered_lines.append(line)
    return "\n".join(filtered_lines)

def split_diff_intelligent(diff, max_lines=1000):
    """
    Découpe le diff en blocs par fichier, puis subdivise chaque bloc s'il est trop volumineux
    (en se basant sur le nombre de lignes).
    
    On suppose que chaque bloc de fichier commence par "diff --git".
    """
    # Séparer le diff en blocs en se basant sur "diff --git"
    blocks = re.split(r'(?=^diff --git)', diff, flags=re.MULTILINE)
    chunks = []
    for block in blocks:
        if not block.strip():
            continue
        # Si le bloc est court, on le garde tel quel
        lines = block.splitlines()
        if len(lines) <= max_lines:
            chunks.append(block)
        else:
            # Si le bloc est trop grand, on le subdivise par tranche de max_lines
            for i in range(0, len(lines), max_lines):
                sub_block = "\n".join(lines[i:i+max_lines])
                chunks.append(sub_block)
    return chunks

import re

def preprocess_diff_with_line_numbers(diff):
    """
    Prend en entrée un diff unifié et renvoie une version annotée
    avec les numéros de ligne du nouveau fichier.

    - Pour les lignes de contexte (commençant par ' '), on affiche le numéro de ligne et incrémente.
    - Pour les lignes ajoutées (commençant par '+'), on affiche le numéro et incrémente.
    - Pour les lignes supprimées (commençant par '-'), on affiche un marqueur "[REMOVED]" sans incrémenter.
    - Les hunk headers (commençant par '@@') sont conservés pour garder la structure.
    
    Retourne une chaîne de caractères avec le diff prétraité.
    """
    lines = diff.splitlines()
    processed_lines = []
    new_line_number = None
    # Expression régulière pour détecter les hunk headers, par exemple: @@ -20,7 +20,8 @@
    hunk_header_pattern = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')

    for line in lines:
        if line.startswith('@@'):
            # Extraire le numéro de départ du nouveau fichier depuis le hunk header
            match = hunk_header_pattern.match(line)
            if match:
                new_line_number = int(match.group(1))
            processed_lines.append(line)
        elif new_line_number is not None:
            if line.startswith(' '):
                # Ligne de contexte
                annotated_line = f"Line {new_line_number}: {line[1:]}"
                processed_lines.append(annotated_line)
                new_line_number += 1
            elif line.startswith('+'):
                # Ligne ajoutée
                annotated_line = f"Line {new_line_number}: {line[1:]}"
                processed_lines.append(annotated_line)
                new_line_number += 1
            elif line.startswith('-'):
                # Ligne supprimée, on indique qu'elle a été supprimée sans incrémenter
                annotated_line = f"[REMOVED] {line[1:]}"
                processed_lines.append(annotated_line)
            else:
                processed_lines.append(line)
        else:
            # Si on n'est pas dans un hunk, on conserve la ligne telle quelle
            processed_lines.append(line)
    
    return "\n".join(processed_lines)