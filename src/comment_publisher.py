import logging
from config import load_config
from comment_publisher_github import publish_review_with_suggestions

def post_comments(comments):
    """
    Publish a single GitHub Pull Request Review containing all suggestions as inline comments.
    Returns True if the API call succeeded.
    """
    config = load_config()

    if config.CI_PLATFORM != "github":
        logging.error("CI platform '%s' not supported for comment publishing.", config.CI_PLATFORM)
        return False

    return publish_review_with_suggestions(comments, config)
