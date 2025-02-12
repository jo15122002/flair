import requests
import logging

def query_llm(diff_chunk, config, params=None):
    """
    Envoie un chunk de diff au serveur LLM (llama.cpp) et renvoie la réponse sous forme de dictionnaire.
    
    :param diff_chunk: Le segment de diff à analyser.
    :param config: La configuration chargée depuis config.py.
    :param params: Un dictionnaire de paramètres supplémentaires (ex: max_tokens, temperature).
    :return: La réponse du LLM sous forme de dictionnaire ou None en cas d'erreur.
    """
    # Valeurs par défaut pour les paramètres si aucun n'est fourni
    if params is None:
        params = {
            "max_tokens": 150,
            "temperature": 0.7
        }
    
    # Construction du payload à envoyer
    payload = {
        "prompt": diff_chunk,
    }
    payload.update(params)
    
    try:
        response = requests.post(config.LLM_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de l'appel au LLM: %s", e)
        return None


# main
if __name__ == "__main__":
    import config as cfg

    # Lecture du fichier de diff
    diff_chunk = "Hello world"

    # Appel au LLM
    response = query_llm(diff_chunk, cfg.load_config())
    if response is not None:
        print(response)
    else:
        print("Erreur lors de l'appel au LLM")