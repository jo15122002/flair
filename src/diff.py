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
    """
    --> On découpe désormais par bloc de fichier (chaque premier 'diff --git').
    --> On regroupe ces blocs en chunks <= max_chars pour éviter de couper en plein milieu d'un fichier.
    """
    if not diff:
        return []

    # 1) Séparer en blocs par fichier
    blocks = []
    current = []
    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git"):
            if current:
                blocks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("".join(current))

    # 2) Regrouper ces blocs en chunks < max_chars
    chunks = []
    chunk = ""
    for blk in blocks:
        if chunk and len(chunk) + len(blk) > max_chars:
            chunks.append(chunk)
            chunk = blk
        else:
            chunk += blk
    if chunk:
        chunks.append(chunk)

    return chunks
