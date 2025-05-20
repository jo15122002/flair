import os
import unittest
from unittest.mock import patch

from src.comment_publisher import post_comments

class DummyConfig:
    CI_PLATFORM = "github"
    GITHUB_TOKEN = "token"
    GITHUB_API_URL = "https://api.github.com"

class TestPostComments(unittest.TestCase):

    @patch("src.comment_publisher.publish_review_with_suggestions")
    @patch("src.config.load_config")
    def test_post_comments_calls_review(self, mock_load_config, mock_publish):
        # Configure le load_config pour renvoyer DummyConfig
        mock_load_config.return_value = DummyConfig
        # Simule un succès de publication
        mock_publish.return_value = True

        os.environ["CI_PLATFORM"] = "github"
        comments = [
            {"file": "a.py", "line": 1, "comment": "First suggestion"},
            {"file": "b.py", "line": 2, "comment": "Second suggestion"},
        ]
        result = post_comments(comments)

        mock_publish.assert_called_once_with(comments, DummyConfig)
        self.assertTrue(result)

    @patch("src.config.load_config")
    def test_post_comments_unsupported_platform(self, mock_load_config):
        class Config:
            CI_PLATFORM = "gitlab"
        mock_load_config.return_value = Config

        comments = []
        result = post_comments(comments)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
