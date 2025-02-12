import requests
import logging

def query_llm(diff_chunk, config, params=None):
    """
    Envoie un chunk de diff, intégré dans un prompt, au serveur LLM et renvoie la réponse.
    """
    if params is None:
        params = {
            "max_tokens": 900,
            "temperature": 0.7
        }
    
    # Construire le prompt complet avec le diff
    prompt = build_llm_prompt(diff_chunk)
    
    payload = {
        "prompt": prompt,
    }
    payload.update(params)
    
    try:
        response = requests.post(config.LLM_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Erreur lors de l'appel au LLM: %s", e)
        return None

def build_llm_prompt(diff):
    """
    Construit le prompt complet à envoyer au LLM en insérant le diff dans le template.
    """
    prompt = f"""
    You are an expert code reviewer specialized in identifying code issues, improvements, and best practices. I will provide you with a code diff from a merge request. Please analyze the diff carefully and provide detailed, actionable feedback. Focus on potential bugs, code readability, security, performance, and maintainability.

    Your response should be in JSON format with the following structure:

    {{
      "comments": [
        {{
          "file": "filename",
          "line": line_number_or_range,
          "comment": "Your feedback on this section."
        }},
        ...
      ]
    }}

    If you do not identify any issues, return an empty "comments" array.

    Here is the diff:
    {diff}
    """
    return prompt.strip()

# main
if __name__ == "__main__":
    import config as cfg

    # Lecture du fichier de diff
    diff_chunk = "Hello world"

    # Appel au LLM
    response = query_llm(diff_chunk, cfg.load_config())
    if response is not None:
        print(response.get("content", []))
    else:
        print("Erreur lors de l'appel au LLM")