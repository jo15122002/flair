import logging
from config import load_config
from comment_publisher_github import publish_comment as publish_github

def post_comments(comments):
    """
    Publie une liste de commentaires sur la pull request en fonction de la plateforme CI/CD.
    
    :param comments: Liste de chaînes de caractères, chaque chaîne étant un commentaire.
    :return: True si tous les commentaires ont été publiés avec succès.
    """
    config = load_config()
    
    if config.CI_PLATFORM == "github":
        for comment in comments:
            if not publish_github(comment, config):
                logging.error("Échec de publication pour le commentaire: %s", comment)
                return False
        return True
    elif config.CI_PLATFORM == "gitlab":
        # À implémenter ultérieurement pour GitLab.
        logging.error("Publication pour GitLab non implémentée.")
        return False
    else:
        raise ValueError(f"Plateforme CI inconnue : {config.CI_PLATFORM}")
