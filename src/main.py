import logging
import json
from config import load_config
from diff_extractor import get_diff_from_pr, filter_diff, split_diff_intelligent
from llm_client import query_llm, extract_json_from_text, adjust_line_number_from_diff
from comment_publisher import post_comments

def main():
    # Chargement de la configuration et initialisation du logging
    config = load_config()
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

    # Filtrer les fichiers de tests et autres exclusions
    diff_filtered = filter_diff(diff)
    
    # 2. Découpage intelligent du diff (par bloc de fichier / par nombre de lignes)
    chunks = split_diff_intelligent(diff_filtered, max_lines=1000)
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
        
        parsed_response = extract_json_from_text(response_content)
        if parsed_response is None:
            logging.error("Impossible d'extraire le JSON du chunk %d.", i+1)
            comments = []
        else:
            comments = parsed_response.get("comments", [])
        
        # Pour chaque commentaire renvoyé, ajuster le numéro de ligne en se basant sur le diff
        for comment in comments:
            reported_line = comment.get("line")
            try:
                reported_line_int = int(reported_line)
            except (ValueError, TypeError):
                logging.warning("Numéro de ligne non valide pour le commentaire: %s", reported_line)
                continue
            adjusted_line = adjust_line_number_from_diff(chunk, reported_line_int)
            comment["line"] = adjusted_line
        
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
