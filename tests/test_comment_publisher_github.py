import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from src.comment_publisher_github import publish_comment

class DummyConfig:
    GITHUB_API_URL = "https://api.github.com"
    GITHUB_TOKEN = "dummy_token"

class TestCommentPublisherGitHub(unittest.TestCase):

    @patch("src.comment_publisher_github.requests.post")
    def test_publish_comment_success(self, mock_post):
        # Configuration des variables d'environnement pour simuler l'environnement GitHub
        os.environ["REPOSITORY_GITHUB"] = "owner/repo"
        os.environ["PR_NUMBER_GITHUB"] = "42"

        # Simuler une réponse réussie de l'API GitHub
        fake_response = MagicMock(status_code=201)
        fake_response.raise_for_status.return_value = None
        mock_post.return_value = fake_response

        # Définir un commentaire structuré comme attendu par la fonction
        comment = {
            "file": "src/main.py",
            "line": 42,
            "comment": "This is a test comment from the LLM feedback."
        }
        result = publish_comment(comment, DummyConfig())
        self.assertTrue(result)

    @patch("src.comment_publisher_github.requests.post")
    def test_publish_comment_failure(self, mock_post):
        # Configuration des variables d'environnement simulées
        os.environ["REPOSITORY_GITHUB"] = "owner/repo"
        os.environ["PR_NUMBER_GITHUB"] = "42"

        # Simuler une exception lors de l'appel HTTP
        mock_post.side_effect = requests.exceptions.RequestException("Error")
        comment = {
            "file": "src/main.py",
            "line": 42,
            "comment": "This is a test comment from the LLM feedback."
        }
        result = publish_comment(comment, DummyConfig())
        self.assertFalse(result)

    def test_publish_comment_missing_env_vars(self):
        # Supprimer les variables d'environnement pour simuler leur absence
        os.environ.pop("REPOSITORY_GITHUB", None)
        os.environ.pop("PR_NUMBER_GITHUB", None)

        comment = {
            "file": "src/main.py",
            "line": 42,
            "comment": "This is a test comment from the LLM feedback."
        }
        result = publish_comment(comment, DummyConfig())
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
