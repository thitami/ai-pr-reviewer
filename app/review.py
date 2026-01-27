# app/review.py

import json
from typing import List
import requests
from openai import OpenAIError
import openai
from pydantic import BaseModel


# === Pydantic model for structured review ===
class AIReview(BaseModel):
    summary: str
    issues: List[str]
    complexity_score: int
    risk_level: str
    recommended_actions: List[str]
    lines_in_diff: int
    error: str = ""  # Optional field for AI errors


# === Core diff review function ===
def review_diff(diff: str) -> dict:
    """
    Review a code diff using AI and heuristics.
    Returns a dictionary with summary, issues, risk level, recommended actions, and metadata.
    """
    try:
        # --- Call OpenAI ---
        ai_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": diff}],
        )
        ai_content = ai_response.choices[0].message.content
        ai_data = json.loads(ai_content)
    except (OpenAIError, json.JSONDecodeError, AttributeError, IndexError):
        # Fallback if AI fails
        ai_data = {
            "summary": "Heuristic pre-review",
            "issues": [],
            "complexity_score": 0,
            "risk_level": "low",
            "recommended_actions": [],
            "error": "AI review failed or returned invalid data",
        }

    # --- Heuristic checks ---
    heuristic_issues = []
    heuristic_actions = []
    risk = ai_data.get("risk_level", "low")

    # Detect debug prints
    if any("print(" in line for line in diff.splitlines()):
        heuristic_issues.append("Debug prints detected")
        heuristic_actions.append("Manual review recommended")
        if risk == "low":
            risk = "medium"

    # Detect TODO/FIXME comments
    if any("TODO" in line or "FIXME" in line for line in diff.splitlines()):
        heuristic_issues.append("Contains TODO/FIXME comments")
        heuristic_actions.append("Manual review recommended")
        if risk != "high":
            risk = "medium"

    # Large PRs
    if len(diff.splitlines()) > 200:
        risk = "high"
        heuristic_actions.append("Manual review recommended")

    # --- Merge AI + heuristic results ---
    ai_data["issues"] = list(set(ai_data.get("issues", []) + heuristic_issues))
    ai_data["recommended_actions"] = list(set(ai_data.get("recommended_actions", []) + heuristic_actions))
    ai_data["risk_level"] = risk
    ai_data["lines_in_diff"] = len(diff.splitlines())

    # Return as dict
    return AIReview(**ai_data).model_dump()


# === GitHub PR review wrapper ===
def review_github_pr(owner: str, repo: str, pr_number: int) -> dict:
    """
    Fetch a GitHub pull request diff and return a structured AI + heuristic review.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        diff_text = resp.text
    except requests.RequestException as e:
        return {"error": f"GitHub API request failed: {e}"}

    # Analyze diff using review_diff
    review_result = review_diff(diff_text)
    return review_result
