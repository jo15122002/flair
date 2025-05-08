import os, logging, requests

def post_per_comment(comments, cfg):
    url = f"{cfg.GITHUB_API_URL}/repos/{cfg.REPOSITORY}/issues/{cfg.PR_NUMBER}/comments"
    hdr = {"Authorization":f"Bearer {cfg.GITHUB_TOKEN}","Accept":"application/vnd.github.v3+json"}
    ok=True
    for c in comments:
        body = f"**{c['file']}:{c['line']}**\n{c['comment']}"
        r = requests.post(url,json={"body":body},headers=hdr)
        try: r.raise_for_status()
        except Exception as e:
            logging.error("failed:",e); ok=False
    return ok

def post_review(comments, cfg):
    # summary + inline suggestions as a single PR Review
    url = f"{cfg.GITHUB_API_URL}/repos/{cfg.REPOSITORY}/pulls/{cfg.PR_NUMBER}/reviews"
    hdr = {"Authorization":f"Bearer {cfg.GITHUB_TOKEN}","Accept":"application/vnd.github.v3+json"}
    # build summary table...
    summary = "## Review Summary\n\n" + f"Generated {len(comments)} suggestions\n\n"
    summary += "|File|Line|Suggestion|\n|--|--|--|\n"
    for c in comments:
        summary += f"|`{c['file']}`|{c['line']}|{c['comment'].splitlines()[0]}|\n"
    # inline
    inline = []
    for c in comments:
        inline.append({
            "path":c["file"],"side":"RIGHT",
            "line":int(c["line"]), "body":c["comment"]
        })
    payload={"body":summary,"event":"COMMENT","comments":inline}
    r = requests.post(url,json=payload,headers=hdr)
    try: r.raise_for_status(); return True
    except Exception as e:
        logging.error("review failed:",e)
        return False
