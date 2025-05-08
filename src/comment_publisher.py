import logging
from config import load_config
from comment_publisher_github import publish_comment as publish_one, publish_review_summary, publish_review_with_suggestions

def post_comments(comments):
    """
    Publish comments on the pull request:
      • If SUMMARY_MODE is enabled, create one GitHub Pull Request Review
        with an overview and all suggestions as inline comments.
      • Otherwise, post one standalone issue comment per suggestion.
    Returns True if all API calls succeeded.
    """
    config = load_config()

    if config.CI_PLATFORM != "github":
        logging.error("CI platform '%s' not supported for comment publishing.", config.CI_PLATFORM)
        return False

    if config.SUMMARY_MODE:
        # Single PR review with summary + inline suggestions
        return publish_review_with_suggestions(comments, config)

    # Default: one issue comment per suggestion
    all_ok = True
    for c in comments:
        ok = publish_comment(c, config)
        if not ok:
            logging.error("Failed to publish comment: %s", c)
            all_ok = False
    return all_ok