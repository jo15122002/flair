import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Current CI/CD platform: 'github' or 'gitlab'
    CI_PLATFORM = os.getenv("CI_PLATFORM", "github")
    
    # LLM configuration
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8080/predict")
    DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))
    
    # GitHub-specific configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
    
    # GitLab-specific configuration (for future extension)
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN", "")
    
    # Patterns to exclude from diff (converted to a list)
    EXCLUDE_PATTERNS = os.getenv("EXCLUDE_PATTERNS", "test,tests,spec").split(',')
    # If true, emit a single summary comment instead of one-per-suggestion
    SUMMARY_MODE = os.getenv("SUMMARY_MODE", "false").lower() in ["true","1","yes"]

def load_config():
    return Config

# For testing purposes
if __name__ == "__main__":
    config = load_config()
    print("LLM_ENDPOINT:", config.LLM_ENDPOINT)
    print("DIFF_CHUNK_SIZE:", config.DIFF_CHUNK_SIZE)
    print("CI_PLATFORM:", config.CI_PLATFORM)
    print("GITHUB_TOKEN:", config.GITHUB_TOKEN)
    print("GITHUB_API_URL:", config.GITHUB_API_URL)
    print("GITLAB_API_URL:", config.GITLAB_API_URL)
    print("GITLAB_PRIVATE_TOKEN:", config.GITLAB_PRIVATE_TOKEN)
