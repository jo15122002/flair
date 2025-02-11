import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Plateforme CI/CD en cours : 'github' ou 'gitlab'
    CI_PLATFORM = os.getenv("CI_PLATFORM", "github")
    
    # LLM
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8080/predict")
    DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))
    
    # Configuration spécifique à GitHub Actions
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
    
    # Configuration spécifique à GitLab (pour une future extension)
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN", "")

def load_config():
    return Config
