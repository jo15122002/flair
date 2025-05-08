import requests
import logging
import json
import re

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
    """
    Injects the diff into the prompt template.
    """
    return PROMPT_TEMPLATE.format(diff=diff)

def call_llm(diff_chunk, cfg):
    """
    Sends a diff chunk to the LLM endpoint and returns the raw text.
    Supports DeepCoder-style choices or a simple 'content' key.
    """
    payload = {"prompt": build_llm_prompt(diff_chunk)}
    try:
        r = requests.post(cfg.LLM_ENDPOINT, json=payload)
        r.raise_for_status()
        data = r.json()
        # DeepCoder-style
        if "choices" in data and isinstance(data["choices"], list):
            return data["choices"][0].get("text", "")
        # fallback
        return data.get("content", "")
    except requests.exceptions.RequestException as e:
        logging.error("Error calling LLM: %s", e)
        return ""

def extract_comments(text):
    """
    Pulls out the 'comments' array from an LLM response string.
    Steps:
      1. Strip out any <think>…</think> blocks and ```json fences```.
      2. Locate the first JSON object or array in the result.
      3. Quote any bare numeric ranges on "line" fields (e.g., 1-48 → "1-48").
      4. Remove trailing commas before } or ].
      5. Parse and return the comments list (or empty list on failure).
    """
    logging.info("LLM response: %s", text)

    # 1) Remove internal think tags and code fences
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'```(?:json)?', '', cleaned)

    # 2) Extract JSON object or array
    match = re.search(r'({[\s\S]*})', cleaned)
    if match:
        snippet = match.group(1)
    else:
        match = re.search(r'(\[[\s\S]*\])', cleaned)
        snippet = match.group(1) if match else cleaned

    # 3) Quote hyphenated ranges on "line" fields
    snippet = re.sub(
        r'("line"\s*:\s*)(\d+\s*-\s*\d+)',
        lambda m: f'{m.group(1)}"{m.group(2).strip()}"',
        snippet
    )

    # 4) Remove trailing commas before } or ]
    snippet = re.sub(r',\s*(\}|])', r'\1', snippet)

    # 5) Attempt JSON parse
    try:
        obj = json.loads(snippet)
        if isinstance(obj, dict):
            return obj.get("comments", [])
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError as e:
        logging.warning("Failed to parse JSON snippet: %s", e)

    logging.warning("Could not extract comments JSON from LLM response.")
    return []
