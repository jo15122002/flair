import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # CI/CD platform: 'github' or 'gitlab'
    CI_PLATFORM = os.getenv("CI_PLATFORM", "github")
    
    # LLM configuration
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8080/predict")
    DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))
    
    # GitHub-specific configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
    
    # GitLab-specific configuration (future extension)
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN", "")
    
    # Patterns to exclude (as a list)
    EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", "test,tests,spec").split(',')
    
    # Optional: Use GitIngest to provide full file context
    USE_GITINGEST = os.getenv("USE_GITINGEST", "false").lower() in ["true", "1", "yes"]

def load_config():
    return Config

if __name__ == "__main__":
    config = load_config()
    print("LLM_ENDPOINT:", config.LLM_ENDPOINT)
    print("DIFF_CHUNK_SIZE:", config.DIFF_CHUNK_SIZE)
    print("CI_PLATFORM:", config.CI_PLATFORM)
    print("GITHUB_TOKEN:", config.GITHUB_TOKEN)
    print("GITHUB_API_URL:", config.GITHUB_API_URL)
    print("USE_GITINGEST:", config.USE_GITINGEST)
