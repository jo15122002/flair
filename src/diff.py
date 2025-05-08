import os, logging, requests, re

def fetch_pr_diff(repo, pr, token):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.text

def filter_diff(diff, patterns):
    out, skip = [], False
    for l in diff.splitlines():
        if l.startswith("diff --git"):
            file = l.split()[2][2:]
            skip = any(p in file.lower() for p in patterns)
        if not skip:
            out.append(l)
    return "\n".join(out)

def split_diff(diff, max_chars):
    if not diff: return []
    return [diff[i:i+max_chars] for i in range(0, len(diff), max_chars)]
