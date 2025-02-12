import logging
import json
from config import load_config
from diff_extractor import get_diff_from_pr, split_diff
from llm_client import query_llm
from comment_publisher import post_comments

def main():
    # Chargement de la configuration et initialisation du logging
    config = load_config()
    logging.info(config)
    if not config:
        logging.error("Erreur lors du chargement de la configuration.")
        return
    logging.basicConfig(level=logging.INFO)
    
    # 1. Récupération du diff via l'API GitHub
    logging.info("Récupération du diff de la pull request via l'API GitHub...")
    diff = get_diff_from_pr()
    if not diff:
        logging.error("Aucun diff récupéré. Vérifiez les variables d'environnement et les permissions.")
        return

    # 2. Segmenter le diff si nécessaire
    chunks = split_diff(diff, config.DIFF_CHUNK_SIZE)
    logging.info("Diff découpé en %d chunk(s).", len(chunks))
    
    all_comments = []
    # 3. Pour chaque chunk, interroger le LLM
    for i, chunk in enumerate(chunks):
        logging.info("Envoi du chunk %d/%d au LLM...", i+1, len(chunks))
        response = query_llm(chunk, config)
        if response is None:
            logging.error("Erreur lors de la réception de la réponse du LLM pour le chunk %d.", i+1)
            continue
        
        response_content = response.get("content")
        if response_content is None:
            logging.error("Réponse du LLM pour le chunk %d vide ou malformée.", i+1)
            continue
        
        try:
            parsed_response = json.loads(response_content)
            comments = parsed_response.get("comments", [])
        except json.JSONDecodeError as e:
            # Gérer le cas où la chaîne n'est pas un JSON valide
            print("Erreur de décodage JSON:", e)
            comments = []
        if comments:
            logging.info("Chunk %d traité : %d commentaire(s) généré(s).", i+1, len(comments))
            all_comments.extend(comments)
        else:
            logging.info("Aucun commentaire généré pour le chunk %d.", i+1)

    if not all_comments:
        logging.info("Aucun commentaire généré par le LLM sur l'ensemble du diff.")
        return

    # 4. Publication des commentaires sur la pull request
    logging.info("Publication des commentaires sur la pull request...")
    if post_comments(all_comments):
        logging.info("Commentaires publiés avec succès.")
    else:
        logging.error("Erreur lors de la publication des commentaires.")

if __name__ == "__main__":
    main()
