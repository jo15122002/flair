import unittest
from unittest.mock import patch, MagicMock
import requests

from src.llm_client import query_llm

class DummyConfig:
    LLM_ENDPOINT = "http://localhost:8080/predict"

class TestLLMClient(unittest.TestCase):

    @patch("src.llm_client.requests.post")
    def test_query_llm_success(self, mock_post):
        # Simulation d'une réponse correcte du LLM
        fake_response = {"response": "Ceci est la réponse du LLM", "comments": []}
        mock_post.return_value = MagicMock(status_code=200, json=lambda: fake_response)
        
        result = query_llm("diff chunk", DummyConfig())
        self.assertEqual(result, fake_response)
    
    @patch("src.llm_client.requests.post")
    def test_query_llm_failure(self, mock_post):
        # Simulation d'une exception lors de l'appel HTTP
        mock_post.side_effect = requests.exceptions.RequestException("Erreur")
        result = query_llm("diff chunk", DummyConfig())
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
