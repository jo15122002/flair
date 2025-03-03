import requests
import logging
import json
import re

def query_llm(diff_chunk, config, params=None):
    """
    Sends a diff chunk (embedded within a prompt) to the LLM server and returns the JSON response.
    """
    if params is None:
        params = {
            "max_tokens": 900,
            "temperature": 0.7
        }
    
    prompt = build_llm_prompt(diff_chunk)
    payload = {"prompt": prompt}
    payload.update(params)
    
    try:
        response = requests.post(config.LLM_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error("Error calling LLM: %s", e)
        return None

def build_llm_prompt(diff):
    """
    Constructs the full prompt to send to the LLM by embedding the diff.
    """
    prompt = f"""
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
    return prompt.strip()

def extract_json_from_text(text):
    """
    Extracts a JSON object from a text string by locating the first '{' and the last '}'.
    If that fails, it attempts to use regex to find a JSON block.
    Returns the parsed dictionary if successful, otherwise None.
    """
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = text[start:end+1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    matches = re.findall(r'{.*}', text, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            return None
    return None

def adjust_line_number_from_diff(diff_chunk, reported_line):
    """
    Adjusts the reported line number from the LLM based on hunk headers in the diff chunk.
    
    Args:
        diff_chunk (str): A diff segment (possibly containing multiple hunks).
        reported_line (int): The line number provided by the LLM.
    
    Returns:
        int: The adjusted line number based on the diff information.
    """
    hunk_regex = re.compile(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
    best_candidate = None
    smallest_distance = None

    for match in hunk_regex.finditer(diff_chunk):
        start_new = int(match.group(1))
        count_new = int(match.group(2)) if match.group(2) is not None else 1
        end_new = start_new + count_new - 1
        
        if start_new <= reported_line <= end_new:
            return reported_line
        
        if reported_line < start_new:
            distance = start_new - reported_line
            candidate = start_new
        else:
            distance = reported_line - end_new
            candidate = end_new
        
        if smallest_distance is None or distance < smallest_distance:
            smallest_distance = distance
            best_candidate = candidate

    return best_candidate if best_candidate is not None else reported_line

# For testing purposes
if __name__ == "__main__":
    from config import load_config
    config = load_config()
    diff_chunk = "Example diff chunk"
    response = query_llm(diff_chunk, config)
    if response is not None:
        print(response.get("content", []))
    else:
        print("Error calling LLM")
