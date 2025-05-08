import logging
from config import load_config
from comment_publisher_github import publish_comment as publish_one, publish_review_summary

def post_comments(comments):
    """
    Publishes comments on the pull request.
    - If SUMMARY_MODE is enabled, posts one overview comment with all suggestions.
    - Otherwise, posts one comment per suggestion.

    :param comments: List of comment dicts with keys 'file', 'line', 'comment', optionally 'context'.
    :return: True if publishing succeeded, False otherwise.
    """
    config = load_config()

    if config.CI_PLATFORM != "github":
        logging.error("CI platform %s not supported for comments.", config.CI_PLATFORM)
        return False

    if config.SUMMARY_MODE:
        # Post a single summarized review comment
        return publish_review_summary(comments, config)

    # Default: one comment per suggestion
    for comment in comments:
        if not publish_one(comment, config):
            logging.error("Failed to publish comment: %s", comment)
            return False
    return True
