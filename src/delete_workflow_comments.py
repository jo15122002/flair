import os
import sys
import requests

def delete_workflow_comments():
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("GITHUB_PR_NUMBER")
    token = os.getenv("GITHUB_TOKEN")
    if not repo or not pr_number or not token:
        print("Les variables d'environnement GITHUB_REPOSITORY, GITHUB_PR_NUMBER et GITHUB_TOKEN doivent être définies.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Erreur lors de la récupération des commentaires :", response.text)
        sys.exit(1)

    comments = response.json()
    for comment in comments:
        comment_id = comment.get("id")
        body = comment.get("body", "")
        # On filtre les commentaires du workflow à l'aide d'un marqueur. Adaptez ce marqueur selon votre implémentation.
        if "LLM Code Review" in body:
            del_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
            del_resp = requests.delete(del_url, headers=headers)
            if del_resp.status_code == 204:
                print(f"Commentaire de workflow {comment_id} supprimé.")
            else:
                print(f"Échec de suppression du commentaire {comment_id} : {del_resp.text}")

if __name__ == "__main__":
    delete_workflow_comments()
