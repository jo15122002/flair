import os
import logging
import requests
import re

def post_per_comment(comments, cfg) -> bool:
    url = f"{cfg.GITHUB_API_URL}/repos/{cfg.REPOSITORY}/issues/{cfg.PR_NUMBER}/comments"
    headers = {
        "Authorization": f"Bearer {cfg.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    ok = True

    for c in comments:
        body = f"**{c['file']}:{c['line']}**\n\n{c['comment']}"
        try:
            resp = requests.post(url, json={"body": body}, headers=headers)
            resp.raise_for_status()
            logging.info("Posted issue comment for %s:%s", c["file"], c["line"])
        except requests.exceptions.RequestException as e:
            logging.error(
                "Failed to post issue comment for %s:%s — %s\nResponse: %s",
                c["file"], c["line"], e, getattr(resp, "text", "")
            )
            ok = False

    return ok

import re
import logging
import requests
from typing import List, Dict, Any, Optional

from config import Config

def get_commit_id(repo: str, pr_number: int, token: str, api_url: str) -> str | None:
    url = f"{api_url}/repos/{repo}/pulls/{pr_number}"
    headers = {'Authorization': f'token {token}'}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur réseau ou HTTP lors de la récupération du commit SHA pour {repo}#{pr_number} : {e}")
        return None

    data = resp.json()
    sha = data.get('head', {}).get('sha')
    if not sha:
        logging.error(f"Aucun SHA trouvé dans la réponse pour {repo}#{pr_number}")
    return sha

def post_per_comment(comments: list[dict[str, Any]], repo: str, pr_number: int, token: str, api_url: str) -> bool:
    success = True
    for c in comments:
        text = c.get('body') or c.get('comment')
        if not text:
            logging.warning(f"Commentaire sans contenu ignoré : {c}")
            continue
        url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"
        payload = {'body': text}
        headers = {'Authorization': f'token {token}'}
        try:
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Impossible de poster le commentaire sur {repo}#{pr_number} : {e}")
            success = False
    return success

def post_summary(summary_body: str, repo: str, pr_number: int, token: str, api_url: str) -> bool:
    url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"
    headers = {'Authorization': f'token {token}'}
    payload = {'body': summary_body}
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la publication du résumé sur {repo}#{pr_number} : {e}")
        return False
    return True

def compute_position_in_diff(diff_chunk: str, target_line: int) -> int | None:
    position = 0
    new_line = None
    for raw in diff_chunk.splitlines():
        position += 1
        m = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', raw)
        if m:
            new_line = int(m.group(1))
            continue
        if new_line is None:
            continue
        if raw.startswith(' ') or raw.startswith('+'):
            if new_line == target_line:
                return position
            new_line += 1
    return None

def build_summary_body(comments: list[dict[str, Any]]) -> str:
    lines = [
        "## 💡 Automated Code Review Summary",
        f"\nI generated **{len(comments)}** suggestions.\n",
        "### ▶️ Inline suggestions",
        "",
        "| # | File | Line | Suggestion |",
        "| - | ---- | ---- | ---------- |"
    ]
    for i, c in enumerate(comments, 1):
        file = c.get('file', '<unknown>')
        line = c.get('line', c.get('position', '<unknown>'))
        text = c.get('body') or c.get('comment') or ''
        lines.append(f"| {i} | `{file}` | {line} | {text} |")
    return "\n".join(lines)

def post_review(comments: list[dict[str, Any]], cfg) -> bool:
    repo = cfg.REPOSITORY
    pr = cfg.PR_NUMBER
    token = cfg.GITHUB_TOKEN
    api_url = cfg.GITHUB_API_URL

    if cfg.SUMMARY_MODE:
        summary = build_summary_body(comments)
        return post_summary(summary, repo, pr, token, api_url)

    # mode inline
    commit_id = get_commit_id(repo, pr, token, api_url)
    if not commit_id:
        logging.error("Aucun commit SHA récupéré ; impossible de faire des commentaires inline.")
        return False

    inline_comments = []
    for c in comments:
        # comment peut contenir 'comment' ou 'body'
        text = c.get('body') or c.get('comment')
        if not text:
            continue
        pos = compute_position_in_diff(c.get('diff_chunk', ''), int(c.get('line', -1))) if isinstance(c.get('line'), int) else None
        if pos:
            inline_comments.append({
                'path': c.get('file'),
                'position': pos,
                'body': text
            })
        else:
            logging.info(f"Suggestion non mappable ignorée : {c}")

    payload = {
        'commit_id': commit_id,
        'body': build_summary_body(comments),
        'event': 'COMMENT',
        'comments': inline_comments
    }
    url = f"{api_url}/repos/{repo}/pulls/{pr}/reviews"
    headers = {'Authorization': f'token {token}'}
    try:
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la création de la review GitHub : {e}")
        return False

    return True