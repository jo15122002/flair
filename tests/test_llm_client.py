import unittest
from unittest.mock import patch, MagicMock
import requests

from src.llm_client import query_llm, build_llm_prompt

class DummyConfig:
    LLM_ENDPOINT = "http://localhost:8080/predict"

class TestLLMClient(unittest.TestCase):

    @patch("src.llm_client.requests.post")
    def test_query_llm_success(self, mock_post):
        fake_response = {"response": "This is the LLM response", "comments": []}
        mock_post.return_value = MagicMock(status_code=200, json=lambda: fake_response)
        
        result = query_llm("diff chunk", DummyConfig())
        self.assertEqual(result, fake_response)
    
    @patch("src.llm_client.requests.post")
    def test_query_llm_failure(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Error")
        result = query_llm("diff chunk", DummyConfig())
        self.assertIsNone(result)

    def test_build_llm_prompt_contains_diff(self):
        diff_sample = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1,3 +1,3 @@"
        prompt = build_llm_prompt(diff_sample)
        self.assertIn(diff_sample, prompt)
        self.assertIn("You are an expert code reviewer", prompt)
        self.assertTrue(prompt.startswith("You are"))
        self.assertTrue(prompt.endswith(diff_sample))

if __name__ == "__main__":
    unittest.main()
