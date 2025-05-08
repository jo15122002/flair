import requests, logging, json, re

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

def call_llm(diff_chunk, cfg):
    payload = {"prompt": PROMPT_TEMPLATE.format(diff=diff_chunk)}
    # add defaults or pull from ENV
    payload.update({"max_tokens":900,"temperature":0.7})
    r = requests.post(cfg.LLM_ENDPOINT, json=payload)
    r.raise_for_status()
    return r.json().get("content","")

def extract_comments(text):
    # simple JSON extraction
    try:
        obj = json.loads(text[text.find("{"):text.rfind("}")+1])
        return obj.get("comments",[])
    except:
        # fallback regex
        m = re.findall(r"{.*}", text, re.DOTALL)
        return json.loads(m[-1]).get("comments",[]) if m else []
