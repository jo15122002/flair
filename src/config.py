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
    TOKEN_GITHUB = os.getenv("TOKEN_GITHUB")
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
    
    # Configuration spécifique à GitLab (pour une future extension)
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN", "")

def load_config():
    return Config

# main
if __name__ == "__main__":
    config = load_config()
    print(config.LLM_ENDPOINT)
    print(config.DIFF_CHUNK_SIZE)
    print(config.CI_PLATFORM)
    print(config.TOKEN_GITHUB)
    print(config.GITHUB_API_URL)
    print(config.GITLAB_API_URL)
    print(config.GITLAB_PRIVATE_TOKEN)