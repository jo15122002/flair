import os
import subprocess
import unittest
import requests
from unittest.mock import patch, MagicMock

from src.diff_extractor import split_diff, get_diff_from_pr, filter_diff, split_diff_intelligent

class TestDiffExtractor(unittest.TestCase):

    @patch("src.diff_extractor.subprocess.run")
    def test_split_diff_normal(self, mock_run):
        # Create a diff string of 250 characters and split into chunks of 100 characters
        diff_str = "a" * 250
        chunk_size = 100
        chunks = [diff_str[i:i+chunk_size] for i in range(0, len(diff_str), chunk_size)]
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "a" * 100)
        self.assertEqual(chunks[1], "a" * 100)
        self.assertEqual(chunks[2], "a" * 50)

    @patch("src.diff_extractor.requests.get")
    def test_get_diff_from_pr_success(self, mock_get):
        os.environ["REPOSITORY_GITHUB"] = "owner/repo"
        os.environ["PR_NUMBER_GITHUB"] = "1"
        os.environ["GITHUB_TOKEN"] = "dummy_token"
        
        fake_diff = "diff --git a/file.py b/file.py\n..."
        fake_response = MagicMock(status_code=200)
        fake_response.text = fake_diff
        fake_response.raise_for_status.return_value = None
        mock_get.return_value = fake_response
        
        diff = get_diff_from_pr()
        self.assertEqual(diff, fake_diff)
    
    @patch("src.diff_extractor.requests.get")
    def test_get_diff_from_pr_failure(self, mock_get):
        os.environ["REPOSITORY_GITHUB"] = "owner/repo"
        os.environ["PR_NUMBER_GITHUB"] = "1"
        os.environ["GITHUB_TOKEN"] = "dummy_token"
        
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        diff = get_diff_from_pr()
        self.assertIsNone(diff)
    
    def test_filter_diff(self):
        sample_diff = (
            "diff --git a/test/example.py b/test/example.py\n"
            "index 1234567..89abcde 100644\n"
            "--- a/test/example.py\n"
            "+++ b/test/example.py\n"
            "@@ -1,3 +1,3 @@\n"
            "-old line\n"
            "+new line\n"
            "diff --git a/src/main.py b/src/main.py\n"
            "index 1234567..89abcde 100644\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -10,3 +10,3 @@\n"
            "-old main\n"
            "+new main\n"
        )
        filtered = filter_diff(sample_diff, exclude_patterns=["test"])
        self.assertNotIn("example.py", filtered)
        self.assertIn("src/main.py", filtered)
    
    def test_split_diff_intelligent(self):
        # Create a diff with multiple blocks
        diff_text = "diff --git a/file1.py b/file1.py\n" + "\n".join(["line"] * 1500) + "\n" \
                    "diff --git a/file2.py b/file2.py\n" + "\n".join(["line"] * 500)
        chunks = split_diff_intelligent(diff_text, max_lines=1000)
        # Expect at least 2 chunks since file1.py is split
        self.assertGreaterEqual(len(chunks), 2)

if __name__ == "__main__":
    unittest.main()
