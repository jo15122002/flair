import logging
from config import load_config
from comment_publisher_github import publish_comment as publish_github

def post_comments(comments):
    """
    Publishes a list of comments to the pull request based on the CI/CD platform.
    
    :param comments: List of comment dictionaries.
    :return: True if all comments are published successfully; otherwise, False.
    """
    config = load_config()
    
    if config.CI_PLATFORM == "github":
        for comment in comments:
            if not publish_github(comment, config):
                logging.error("Failed to publish comment: %s", comment)
                return False
        return True
    elif config.CI_PLATFORM == "gitlab":
        logging.error("Publishing for GitLab is not implemented yet.")
        return False
    else:
        raise ValueError(f"Unknown CI platform: {config.CI_PLATFORM}")
