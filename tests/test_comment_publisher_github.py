import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from src.comment_publisher_github import publish_comment

class DummyConfig:
    GITHUB_API_URL = "https://api.github.com"
    TOKEN_GITHUB = "dummy_token"

class TestCommentPublisherGitHub(unittest.TestCase):
    
    @patch("src.comment_publisher_github.requests.post")
    def test_publish_comment_success(self, mock_post):
        # Configurer les variables d'environnement simulées
        os.environ["GITHUB_REPOSITORY"] = "owner/repo"
        os.environ["GITHUB_PR_NUMBER"] = "42"
        
        # Simulation d'une réponse réussie de l'API
        fake_response = MagicMock(status_code=201)
        fake_response.raise_for_status.return_value = None
        mock_post.return_value = fake_response
        
        result = publish_comment("Test commentaire", DummyConfig())
        self.assertTrue(result)
    
    @patch("src.comment_publisher_github.requests.post")
    def test_publish_comment_failure(self, mock_post):
        # Configurer les variables d'environnement simulées
        os.environ["GITHUB_REPOSITORY"] = "owner/repo"
        os.environ["GITHUB_PR_NUMBER"] = "42"
        
        # Simuler une exception lors de l'appel HTTP
        mock_post.side_effect = requests.exceptions.RequestException("Erreur")
        
        result = publish_comment("Test commentaire", DummyConfig())
        self.assertFalse(result)
    
    def test_missing_env_variables(self):
        # Supprimer les variables d'environnement pour ce test
        os.environ.pop("GITHUB_REPOSITORY", None)
        os.environ.pop("GITHUB_PR_NUMBER", None)
        
        result = publish_comment("Test commentaire", DummyConfig())
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
