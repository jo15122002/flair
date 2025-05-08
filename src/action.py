import logging
from config import load_config
from diff import fetch_pr_diff, filter_diff, split_diff
from llm import call_llm, extract_comments
from publish import post_per_comment, post_review

def main():
    cfg = load_config()
    logging.basicConfig(level=logging.INFO)

    diff = fetch_pr_diff(cfg.REPOSITORY, cfg.PR_NUMBER, cfg.GITHUB_TOKEN)
    diff = filter_diff(diff, cfg.EXCLUDE_PATTERNS)
    chunks = split_diff(diff, cfg.DIFF_CHUNK_SIZE)
    all_comments=[]
    for i,ch in enumerate(chunks,1):
        logging.info("Chunk %d/%d",i,len(chunks))
        reply = call_llm(ch, cfg)
        all_comments += extract_comments(reply)

    if not all_comments:
        logging.info("No suggestions generated.")
        return

    if cfg.SUMMARY_MODE:
        success = post_review(all_comments, cfg)
    else:
        success = post_per_comment(all_comments, cfg)

    if success:
        logging.info("Done.")
    else:
        logging.error("Publishing failed.")

if __name__=="__main__":
    main()
