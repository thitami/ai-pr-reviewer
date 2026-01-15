# app/review.py
import os
import json
import requests
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SYSTEM_PROMPT = """
You are a senior software engineer reviewing pull requests.

Return strictly valid JSON with:
{
  "summary": "...",
  "issues": ["..."],
  "complexity_score": 1-10,
  "risk_level": "low|medium|high",
  "recommended_actions": ["..."]
}
"""


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch GitHub PR diff."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"GitHub API error {resp.status_code}: {resp.text}")

    return resp.text


def review_diff(diff: str) -> dict:
    """Send diff to OpenAI and return structured review."""
    lines = diff.splitlines()
    estimated_time = max(1, len(lines) // 10)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Review this diff:\n{diff}"}
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        data["lines_in_diff"] = len(lines)
        data["estimated_human_review_time_min"] = estimated_time
        return data

    except Exception as e:
        return {
            "summary": "",
            "issues": [],
            "lines_in_diff": len(lines),
            "estimated_human_review_time_min": estimated_time,
            "error": str(e),
        }


def review_github_pr(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR diff and return AI review."""
    diff = fetch_pr_diff(owner, repo, pr_number)
    return review_diff(diff)
