import os
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env
load_dotenv()

class Config:
    # URL du serveur LLM (llama.cpp)
    LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:8080/predict")
    
    # URL de l'API de la plateforme de gestion de code (exemple GitLab)
    GITLAB_API_URL = os.getenv("GITLAB_API_URL", "https://gitlab.example.com/api/v4")
    
    # Token pour l'API GitLab
    GITLAB_PRIVATE_TOKEN = os.getenv("GITLAB_PRIVATE_TOKEN", "")
    
    # Taille maximum d'un diff à traiter en un seul morceau (en nombre de caractères)
    DIFF_CHUNK_SIZE = int(os.getenv("DIFF_CHUNK_SIZE", "10000"))

def load_config():
    return Config
