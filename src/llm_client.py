import requests
import logging
import json
import re

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

import json
import re

def extract_json_from_text(text):
    """
    Extrait la sous-chaîne JSON contenue dans le texte.
    Cette fonction recherche la première occurrence de '{' et la dernière de '}'.
    Si cela échoue, elle utilise une regex pour essayer de trouver un objet JSON.
    Retourne le dictionnaire JSON si trouvé, sinon None.
    """
    # Option 1 : Extraire la portion entre la première '{' et la dernière '}'
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # En cas d'erreur, on passe à l'approche regex
            pass

    # Option 2 : Utiliser une regex pour repérer un bloc JSON
    matches = re.findall(r'{.*}', text, re.DOTALL)
    if matches:
        # Par exemple, prendre le dernier match (celui qui semble le plus complet)
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            return None
    return None

def adjust_line_number_from_diff(diff_chunk, reported_line):
    """
    Ajuste le numéro de ligne rapporté par le LLM en se basant sur les hunk headers du diff.
    
    Args:
        diff_chunk (str): Un segment de diff (contenant éventuellement plusieurs hunks).
        reported_line (int): Le numéro de ligne fourni par le LLM (supposé concerner le nouveau fichier).
    
    Returns:
        int: Le numéro de ligne ajusté basé sur les informations du diff.
    """
    # Expression régulière pour extraire le header d'un hunk, par exemple:
    # @@ -10,7 +15,8 @@
    hunk_regex = re.compile(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    
    best_candidate = None
    smallest_distance = None

    # Parcourir chaque hunk dans le diff
    for match in hunk_regex.finditer(diff_chunk):
        start_new = int(match.group(1))
        count_new = int(match.group(2)) if match.group(2) is not None else 1
        end_new = start_new + count_new - 1
        
        # Si le numéro rapporté se trouve dans ce hunk, on le renvoie directement
        if start_new <= reported_line <= end_new:
            return reported_line
        
        # Sinon, calculer la distance par rapport à ce hunk
        if reported_line < start_new:
            distance = start_new - reported_line
            candidate = start_new
        else:
            distance = reported_line - end_new
            candidate = end_new
        
        if smallest_distance is None or distance < smallest_distance:
            smallest_distance = distance
            best_candidate = candidate

    # Si aucun hunk n'est trouvé, on renvoie le numéro rapporté tel quel
    return best_candidate if best_candidate is not None else reported_line

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