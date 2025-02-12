import os
import requests
import logging

def publish_comment(comment, config):
    """
    Publie un commentaire sur une pull request GitHub.
    
    :param comment: Texte du commentaire à publier.
    :param config: Configuration chargée depuis config.py.
    :return: True si le commentaire est publié avec succès, sinon False.
    """
    # Récupération des informations nécessaires
    repo = os.getenv("GITHUB_REPOSITORY")  # Format attendu : "owner/repo"
    pr_number = os.getenv("GITHUB_PR_NUMBER")  # Doit être défini dans l'environnement CI
    if not repo or not pr_number:
        logging.error("Les variables GITHUB_REPOSITORY et GITHUB_PR_NUMBER doivent être définies.")
        return False

    # Construire l'URL de l'API pour poster le commentaire sur la PR
    url = f"{config.GITHUB_API_URL}/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"body": comment}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.info("Commentaire publié avec succès sur la PR #%s.", pr_number)
        return True
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de la publication du commentaire : %s", e)
        return False
    
# main
if __name__ == "__main__":
    import config as cfg

    # Exemple de commentaire à publier
    comment = "Hello world!"
    
    # Publication du commentaire
    if publish_comment(comment, cfg.load_config()):
        print("Commentaire publié avec succès.")
    else:
        print("Erreur lors de la publication du commentaire.")
