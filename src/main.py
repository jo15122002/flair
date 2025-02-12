import logging
from src.config import load_config
from src.diff_extractor import get_diff, split_diff
from src.llm_client import query_llm
from src.comment_publisher import post_comments

def main():
    # Configuration et logging
    config = load_config()
    logging.basicConfig(level=logging.INFO)
    
    # 1. Extraction du diff
    logging.info("Extraction du diff de la merge request...")
    diff = get_diff(config)
    if not diff:
        logging.error("Aucun diff extrait. Vérifiez la configuration et les variables d'environnement.")
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
        
        # On suppose que le LLM renvoie un JSON avec une clé "comments" contenant une liste de commentaires
        comments = response.get("comments", [])
        if comments:
            logging.info("Chunk %d traité : %d commentaire(s) généré(s).", i+1, len(comments))
            all_comments.extend(comments)
        else:
            logging.info("Aucun commentaire généré pour le chunk %d.", i+1)

    if not all_comments:
        logging.info("Aucun commentaire généré par le LLM sur l'ensemble du diff.")
        return

    # 4. Publication des commentaires
    logging.info("Publication des commentaires sur la pull request...")
    if post_comments(all_comments):
        logging.info("Commentaires publiés avec succès.")
    else:
        logging.error("Erreur lors de la publication des commentaires.")

if __name__ == "__main__":
    main()
