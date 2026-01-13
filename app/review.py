import os
import requests
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SYSTEM_PROMPT = "You are a senior staff engineer doing strict pull request reviews."

def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"GitHub API error: {resp.status_code} {resp.text}")
    return resp.text

def review_diff(diff: str) -> str:
    # Call OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this git diff:\n{diff}"}
        ]
    )
    return response.choices[0].message["content"]

# Helper to fetch PR and review in one call
def review_github_pr(owner: str, repo: str, pr_number: int) -> str:
    diff = fetch_pr_diff(owner, repo, pr_number)
    return review_diff(diff)
