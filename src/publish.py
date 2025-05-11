import os
import logging
import requests
import re

def post_per_comment(comments, cfg) -> bool:
    """
    Posts one standalone issue comment per suggestion.
    """
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

def get_commit_id(repo: str, pr: str, token: str, api_url: str) -> str | None:
    """
    Retrieves the SHA of the pull request's head commit via the GitHub API.
    """
    url = f"{api_url}/repos/{repo}/pulls/{pr}"
    headers = {
        "Authorization":        f"Bearer {token}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json().get("head", {}).get("sha")
    except requests.RequestException as e:
        logging.warning("Could not fetch PR head SHA: %s", e)
        return None

def post_summary(comments, cfg) -> bool:
    """
    Posts a single issue comment with a summary table of all suggestions.
    """
    url = f"{cfg.GITHUB_API_URL}/repos/{cfg.REPOSITORY}/issues/{cfg.PR_NUMBER}/comments"
    headers = {
        "Authorization": f"Bearer {cfg.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    total = len(comments)
    lines = [
        "## 💡 Automated Code Review Summary",
        "",
        f"I generated **{total}** suggestion{'s' if total > 1 else ''}.",
        "",
        "| # | File | Line | Suggestion |",
        "| - | ---- | ---- | ---------- |"
    ]
    for idx, c in enumerate(comments, start=1):
        preview = c["comment"].splitlines()[0].replace("|", "\\|")
        lines.append(f"| {idx} | `{c['file']}` | {c['line']} | {preview} |")

    body = "\n".join(lines)
    try:
        resp = requests.post(url, json={"body": body}, headers=headers)
        resp.raise_for_status()
        logging.info("❖ Posted summary issue comment with %d entries.", total)
        return True
    except requests.exceptions.RequestException as e:
        logging.error("❌ Failed to post summary comment: %s\nResponse: %s",
                      e, getattr(resp, "text", ""))
        return False


def compute_position_in_diff(diff_chunk: str, target_line: int) -> int | None:
    """
    Scan `diff_chunk` to find the diff-line position for `target_line` in the new file.
    Returns the 1-based position within the diff, or None if not found.
    """
    hunk_regex = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)
    lines = diff_chunk.splitlines()
    position = 0
    new_line = None

    for raw in lines:
        position += 1
        if raw.startswith('@@'):
            m = hunk_regex.match(raw)
            if m:
                new_line = int(m.group(1))
        elif new_line is not None:
            if raw.startswith(' ') or raw.startswith('+'):
                if new_line == target_line:
                    return position
                new_line += 1
            # deletions ('-') do not advance new_file_line
    return None


def post_review(comments: list[dict], cfg) -> bool:
    """
    Create a GitHub Pull Request Review, separating valid inline suggestions
    and logging/skipping those qui ne matche pas le diff.
    """
    repo    = cfg.REPOSITORY
    pr      = cfg.PR_NUMBER
    token   = cfg.GITHUB_TOKEN
    api_url = cfg.GITHUB_API_URL.rstrip('/')

    # Récupérer ou non le commit_id
    commit_id = os.getenv("GITHUB_HEAD_SHA") or os.getenv("GITHUB_SHA")
    if not commit_id:
        commit_id = get_commit_id(repo, pr, token, api_url)
    if commit_id:
        logging.info("Using commit_id %s for review", commit_id)
    else:
        logging.info("No commit_id provided; defaulting to latest commit")

    url = f"{api_url}/repos/{repo}/pulls/{pr}/reviews"
    headers = {
        "Authorization":        f"Bearer {token}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    inline_comments = []
    skipped = []

    for c in comments:
        # Vérifier les clés indispensables
        if not all(k in c for k in ("file", "line", "comment")):
            skipped.append((c, "missing file/line/comment"))
            continue

        raw_line = str(c["line"])
        first_part = raw_line.split('-', 1)[0]
        try:
            line_no = int(first_part)
        except ValueError:
            skipped.append((c, f"invalid line {raw_line!r}"))
            continue

        pos = compute_position_in_diff(c.get("_chunk", ""), line_no)
        if pos is None:
            skipped.append((c, "cannot map to diff"))
        else:
            inline_comments.append({
                "path":     c["file"],
                "position": pos,
                "body":     c["comment"]
            })

    # Construction du corps du review
    body_lines = [
        "## 💡 Automated Code Review Summary",
        "",
        f"I generated **{len(comments)}** suggestion{'s' if len(comments) > 1 else ''}.",
        ""
    ]

    if inline_comments:
        body_lines += [
            "### ▶️ Inline suggestions",
            "",
            "| # | File | Line | Suggestion |",
            "| - | ---- | ---- | ---------- |"
        ]
        for idx, ic in enumerate(inline_comments, start=1):
            file_ = ic["path"]
            # On récupère la ligne à partir du commentaire original
            # (pas besoin de la clé "line" ici car elle n'est pas envoyée à GitHub)
            raw_comment = next((c for c in comments if c["file"] == file_ and compute_position_in_diff(c.get("_chunk",""), int(str(c["line"]).split("-",1)[0])) == ic["position"]), None)
            line_ = raw_comment["line"] if raw_comment else "?"
            text  = ic["body"].splitlines()[0].replace("|", "\\|")
            body_lines.append(f"| {idx} | `{file_}` | {line_} | {text} |")

    if skipped:
        body_lines += [
            "",
            "### ⚠️ Skipped suggestions",
            ""
        ]
        for c, reason in skipped:
            file_ = c.get("file", "<unknown>")
            line_ = c.get("line", "<no line>")
            text  = c.get("comment", "<no comment>").splitlines()[0].replace("|", "\\|")
            body_lines.append(f"- **{file_}** (line {line_}): {text} — _{reason}_")

    payload = {
        "body":     "\n".join(body_lines),
        "event":    "COMMENT",
        "comments": inline_comments
    }
    if commit_id:
        payload["commit_id"] = commit_id

    logging.debug("Payload for review creation:\n%s", payload)
    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        logging.info("✅ PR review created with %d inline comment(s).", len(inline_comments))
        return True

    except requests.RequestException as e:
        text = getattr(e.response, "text", "")
        logging.error("❌ Review creation failed: %s\nResponse: %s", e, text)
        logging.error("❗ Review payload was:\n%s", payload)
        return False