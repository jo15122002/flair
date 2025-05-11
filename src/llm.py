import requests
import logging
import json
import re
import ast

PROMPT_TEMPLATE = """
You are an expert code reviewer specialized in identifying code issues.
Below is a code diff with explicit line numbers. Please analyze the diff carefully and provide detailed, actionable feedback.
**Important:** Use the provided line numbers exactly as shown and do not shift them.

Your response should be in JSON format with the following structure:

{{
  "comments": [
    {{
      "file": "filename",
      "line": "exact line number or range (e.g., 42 or 40-45)",
      "comment": "Your feedback on this section."
    }},
    ...
  ]
}}

Here is the diff:
{diff}
"""

def build_llm_prompt(diff):
    return PROMPT_TEMPLATE.format(diff=diff)

def call_llm(diff_chunk, cfg):
    """
    Sends a diff chunk to the LLM endpoint and returns the raw text.
    Supports DeepCoder-style 'choices' or a simple 'content' key.
    """
    payload = {"prompt": build_llm_prompt(diff_chunk)}
    try:
        r = requests.post(cfg.LLM_ENDPOINT, json=payload)
        r.raise_for_status()
        data = r.json()
        if "choices" in data and isinstance(data["choices"], list):
            return data["choices"][0].get("text", "")
        return data.get("content", "")
    except requests.exceptions.RequestException as e:
        logging.error("Error calling LLM: %s", e)
        return ""

def extract_comments(text: str) -> list[dict]:
    """
    Extrait la liste 'comments' d'un retour de LLM, même si :
      - des ranges numériques non-quotés subsistent (e.g. 1-53),
      - il y a des virgules superflues,
      - ou des fences Markdown entourent le JSON.

    Retourne une liste vide en cas d’échec complet.
    """
    # 1) Enlever les balises <think>…</think>
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)

    # 2) Extraire le JSON dans un bloc ```json ... ```
    m = re.search(r'```json\s*([\s\S]*?)```', cleaned)
    if m:
        candidate = m.group(1)
    else:
        # 3) Supprimer toutes les fences ```...```
        no_fences = re.sub(r'```[\s\S]*?```', '', cleaned)
        # 4) Trouver le premier {...}
        m2 = re.search(r'\{[\s\S]*\}', no_fences)
        if not m2:
            logging.warning("No JSON object found in LLM response.")
            return []
        candidate = m2.group(0)

    # **DEBUG**: afficher le JSON candidat
    logging.debug("Candidate JSON for comments parsing:\n%s", candidate)

    # 5) Quote tous les ranges numériques X-Y → "X-Y"
    candidate = re.sub(
        r'(?P<prefix>:\s*)(?P<a>\d+)\s*-\s*(?P<b>\d+)(?P<suffix>\s*[,\}])',
        lambda m: f'{m.group("prefix")}"{m.group("a")}-{m.group("b")}"{m.group("suffix")}',
        candidate
    )

    # 6) Enlever virgules finales avant } ou ]
    candidate = re.sub(r',\s*(\}|])', r'\1', candidate)

    # 7) Essayer json.loads
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as e:
        logging.warning("Failed json.loads: %s", e)
        # 8) Fallback ast.literal_eval
        try:
            obj = ast.literal_eval(candidate)
        except Exception as e2:
            logging.error("Failed ast.literal_eval: %s", e2)
            return []

    # 9) Extraire la liste
    if isinstance(obj, dict) and isinstance(obj.get("comments"), list):
        comments = obj["comments"]
    elif isinstance(obj, list):
        comments = obj
    else:
        logging.warning("Parsed object has no 'comments' list.")
        return []

    # 10) Log du nombre de commentaires extraits
    logging.info("Extracted %d comment(s) from LLM response.", len(comments))

    return comments