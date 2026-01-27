# app/main.py
import logging
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from app.review import review_github_pr
from app.monitoring import MetricsMiddleware, get_metrics
from requests.exceptions import RequestException

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-pr-reviewer")

# FastAPI app
app = FastAPI(
    title="AI PR Reviewer",
    description="Fetch GitHub PR diffs and get structured AI code reviews.",
    version="1.0.0",
)

# Add monitoring middleware
app.add_middleware(MetricsMiddleware)


# === Request model ===
class PRRequest(BaseModel):
    owner: str = Field(..., min_length=1, description="GitHub repository owner")
    repo: str = Field(..., min_length=1, description="Repository name")
    pr_number: int = Field(..., gt=0, description="Pull request number")


# === Health check endpoints ===
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "ai-pr-reviewer"
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes."""
    # Add checks for dependencies (OpenAI API, etc.)
    return {
        "status": "ready",
        "service": "ai-pr-reviewer"
    }


@app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics()


# === Review endpoint ===
@app.post("/review", summary="Review a GitHub pull request", tags=["Review"])
async def review_pr(pr_request: PRRequest):
    """
    Fetch a GitHub pull request diff and get AI-generated structured review.

    Returns:
        dict with keys:
            - success: bool
            - analysis: dict (layered heuristic + AI review)
            - pr: dict of PR info
            - error: str if any failure occurred
    """
    logger.info(f"Review requested: {pr_request.owner}/{pr_request.repo} PR#{pr_request.pr_number}")

    try:
        review_data = review_github_pr(
            pr_request.owner,
            pr_request.repo,
            pr_request.pr_number
        )
        # If GitHub returned partial/failure info, escalate as HTTP 502
        if review_data.get("error"):
            logger.warning(f"Partial review due to error: {review_data['error']}")
        return {
            "success": True,
            "analysis": review_data,
            "pr": {
                "owner": pr_request.owner,
                "repo": pr_request.repo,
                "pr_number": pr_request.pr_number
            }
        }

    except RequestException as e:
        logger.error(f"GitHub API error: {e}")
        raise HTTPException(status_code=502, detail=f"GitHub API failure: {e}")

    except Exception as e:
        logger.exception(f"Unexpected error reviewing PR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")