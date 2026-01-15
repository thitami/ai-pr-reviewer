# app/main.py
"""
main.py

FastAPI application for AI-powered GitHub PR reviews.
"""

import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from app.review import review_github_pr

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-pr-reviewer")

# FastAPI app
app = FastAPI(
    title="AI PR Reviewer",
    description="Fetch GitHub PR diffs and get structured AI code reviews.",
    version="1.0.0",
)


# Pydantic request model
class PRRequest(BaseModel):
    owner: str = Field(..., min_length=1, description="GitHub repository owner")
    repo: str = Field(..., min_length=1, description="Repository name")
    pr_number: int = Field(..., gt=0, description="Pull request number")


@app.post("/review", summary="Review a GitHub pull request")
async def review_pr(pr_request: PRRequest):
    """
    Fetch a GitHub pull request diff and get AI-generated structured review.

    Returns:
        dict with keys:
            - success: bool
            - review: dict (summary, issues, lines, estimated human review time)
            - pr: dict of PR info
            - error: str if failed
    """
    logger.info(f"Review requested: {pr_request.owner}/{pr_request.repo} PR#{pr_request.pr_number}")

    try:
        review_data = review_github_pr(
            pr_request.owner,
            pr_request.repo,
            pr_request.pr_number
        )
        return {
            "success": True,
            "analysis": review_data,
            "pr": {
                "owner": pr_request.owner,
                "repo": pr_request.repo,
                "pr_number": pr_request.pr_number
            }
        }

    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        return {
            "success": False,
            "error": str(e)
        }
