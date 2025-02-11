import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock

from src.diff_extractor import get_diff, split_diff

class TestDiffExtractor(unittest.TestCase):

    @patch('src.diff_extractor.subprocess.run')
    def test_get_diff_success(self, mock_run):
        # Configurer les variables d'environnement
        os.environ['GITHUB_HEAD_REF'] = 'feature-branch'
        os.environ['GITHUB_BASE_REF'] = 'main'
        
        # Simuler la commande git fetch (premier appel) et git diff (deuxième appel)
        fake_diff = (
            "diff --git a/file.txt b/file.txt\n"
            "index 1234567..89abcde 100644\n"
            "--- a/file.txt\n"
            "+++ b/file.txt\n"
            "@@ -1,3 +1,3 @@\n"
            "-old line\n"
            "+new line"
        )
        # Premier appel (fetch) retourne None, le second (diff) retourne un objet avec stdout
        mock_fetch = MagicMock(return_value=None)
        mock_diff = MagicMock()
        mock_diff.stdout = fake_diff
        mock_run.side_effect = [mock_fetch.return_value, mock_diff]
        
        diff = get_diff(None)
        self.assertEqual(diff, fake_diff)
        
    @patch('src.diff_extractor.subprocess.run')
    def test_get_diff_failure(self, mock_run):
        # Configurer les variables d'environnement
        os.environ['GITHUB_HEAD_REF'] = 'feature-branch'
        os.environ['GITHUB_BASE_REF'] = 'main'
        
        # Simuler une erreur lors de l'exécution de git (par exemple pour git fetch ou git diff)
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        diff = get_diff(None)
        self.assertIsNone(diff)
        
    def test_get_diff_no_env(self):
        # S'assurer que si les variables d'environnement ne sont pas définies, la fonction retourne None
        os.environ.pop('GITHUB_HEAD_REF', None)
        os.environ.pop('GITHUB_BASE_REF', None)
        
        diff = get_diff(None)
        self.assertIsNone(diff)
        
    def test_split_diff_empty(self):
        # Teste split_diff avec un diff vide
        self.assertEqual(split_diff("", 100), [])
        
    def test_split_diff_normal(self):
        # Créer un diff de 250 caractères et découper en chunks de 100 caractères
        diff_str = "a" * 250
        chunk_size = 100
        chunks = split_diff(diff_str, chunk_size)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "a" * 100)
        self.assertEqual(chunks[1], "a" * 100)
        self.assertEqual(chunks[2], "a" * 50)

if __name__ == '__main__':
    unittest.main()
