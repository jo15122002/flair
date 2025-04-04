import os
import sys
import requests

def delete_all_pr_comments():
    """
    Deletes all comments from a pull request.
    Requires the environment variables: REPOSITORY_GITHUB, PR_NUMBER_GITHUB, and GITHUB_TOKEN.
    """
    repo = os.getenv("REPOSITORY_GITHUB")
    pr_number = os.getenv("PR_NUMBER_GITHUB")
    token = os.getenv("GITHUB_TOKEN")
    if not repo or not pr_number or not token:
        print("Environment variables REPOSITORY_GITHUB, PR_NUMBER_GITHUB and GITHUB_TOKEN must be set.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error retrieving comments:", response.text)
        sys.exit(1)

    comments = response.json()
    for comment in comments:
        comment_id = comment.get("id")
        del_url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
        del_resp = requests.delete(del_url, headers=headers)
        if del_resp.status_code == 204:
            print(f"Comment {comment_id} deleted.")
        else:
            print(f"Failed to delete comment {comment_id}: {del_resp.text}")

if __name__ == "__main__":
    delete_all_pr_comments()
