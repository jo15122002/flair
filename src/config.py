# src/config.py

import os
from dotenv import load_dotenv

# Charge automatiquement les variables d'environnement depuis un fichier .env
load_dotenv()

class Config:
    def __init__(self):
        # GitHub token
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN is not set in the environment")
        self.GITHUB_TOKEN = token

        # GitHub API URL (default to GitHub.com)
        self.GITHUB_API_URL = os.getenv('GITHUB_API_URL', 'https://api.github.com')

        # Repository: support both REPOSITORY and REPOSITORY_GITHUB
        repo = os.getenv('REPOSITORY') or os.getenv('REPOSITORY_GITHUB')
        if not repo:
            raise ValueError("REPOSITORY or REPOSITORY_GITHUB is not set in the environment")
        self.REPOSITORY = repo

        # Pull request number: support both PR_NUMBER and PR_NUMBER_GITHUB
        pr = os.getenv('PR_NUMBER') or os.getenv('PR_NUMBER_GITHUB')
        if not pr:
            raise ValueError("PR_NUMBER or PR_NUMBER_GITHUB is not set in the environment")
        try:
            self.PR_NUMBER = int(pr)
        except ValueError:
            raise ValueError("PR_NUMBER must be an integer")

        # LLM endpoint
        llm = os.getenv('LLM_ENDPOINT')
        if not llm:
            raise ValueError("LLM_ENDPOINT is not set in the environment")
        self.LLM_ENDPOINT = llm

        # Diff chunking
        try:
            self.DIFF_CHUNK_SIZE = int(os.getenv('DIFF_CHUNK_SIZE', '5000'))
        except ValueError:
            raise ValueError("DIFF_CHUNK_SIZE must be an integer")

        # Exclude patterns
        patterns = os.getenv('EXCLUDE_PATTERNS', '')
        self.EXCLUDE_PATTERNS = [p.strip() for p in patterns.split(',') if p.strip()]

        # Summary mode
        self.SUMMARY_MODE = os.getenv('SUMMARY_MODE', 'true').lower() in ('1', 'true', 'yes')

def load_config() -> Config:
    cfg = Config()

    # GitHub
    cfg.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    cfg.GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
    # Fallback sur l'ancienne variable REPOSITORY pour compatibilité
    cfg.REPOSITORY_GITHUB = os.getenv("REPOSITORY_GITHUB", os.getenv("REPOSITORY", ""))
    # Conversion de PR_NUMBER en entier, avec erreur si invalide
    pr_str = os.getenv("PR_NUMBER_GITHUB", os.getenv("PR_NUMBER", ""))
    try:
        cfg.PR_NUMBER_GITHUB = int(pr_str)
    except ValueError:
        raise RuntimeError(f"PR_NUMBER_GITHUB invalide ou manquant : {pr_str!r}")

    # LLM
    cfg.LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")
    cfg.DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))
    cfg.EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", "test,tests,spec").split(",")

    # Publication (mode résumé vs par-commentaire)
    cfg.SUMMARY_MODE = os.getenv("SUMMARY_MODE", "false").lower() in ("true", "1", "yes")

    return cfg
