import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # GitHub
    GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL  = os.getenv("GITHUB_API_URL", "https://api.github.com")
    REPOSITORY      = os.getenv("REPOSITORY")
    PR_NUMBER       = os.getenv("PR_NUMBER")

    # LLM
    LLM_ENDPOINT    = os.getenv("LLM_ENDPOINT")
    DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))
    EXCLUDE_PATTERNS= os.getenv("EXCLUDE_PATTERNS","test,tests,spec").split(',')

    # Summary vs per-comment
    SUMMARY_MODE    = os.getenv("SUMMARY_MODE","false").lower() in ("true","1","yes")

def load_config():
    return Config