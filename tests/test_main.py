import pytest, json, os
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from requests.exceptions import RequestException

from app.main import app

client = TestClient(app)
os.environ["OPENAI_API_KEY"] = "test"  # Prevent OpenAIError

# Sample request payload
sample_payload = {
    "owner": "thitami",
    "repo": "ai-pr-reviewer",
    "pr_number": 1
}


def test_review_pr_success():
    """Test /review endpoint returns expected structure on success."""
    mock_review_data = {
        "summary": "Adds logging",
        "issues": ["Missing tests"],
        "complexity_score": 3,
        "risk_level": "medium",  # merged with heuristic
        "recommended_actions": ["Add unit tests", "Manual review recommended"],
        "lines_in_diff": 1,
        "estimated_human_review_time_min": 1,
        "error": None
    }

    with patch("app.main.review_github_pr", return_value=mock_review_data):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"] == mock_review_data
    assert data["pr"]["owner"] == sample_payload["owner"]
    assert data["pr"]["repo"] == sample_payload["repo"]
    assert data["pr"]["pr_number"] == sample_payload["pr_number"]


def test_review_pr_partial_error():
    """Test /review returns success but includes AI/heuristic errors."""
    mock_review_data = {
        "summary": "Adds logging",
        "issues": ["Missing tests"],
        "complexity_score": 3,
        "risk_level": "medium",
        "recommended_actions": ["Add unit tests", "Manual review recommended"],
        "lines_in_diff": 1,
        "estimated_human_review_time_min": 1,
        "error": "AI model timed out"
    }

    with patch("app.main.review_github_pr", return_value=mock_review_data):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 200
    data = response.json()
    # Endpoint is still successful
    assert data["success"] is True
    assert data["analysis"]["error"] == "AI model timed out"


def test_review_pr_github_failure():
    """Test /review endpoint raises 502 if GitHub API fails."""
    with patch("app.main.review_github_pr", side_effect=RequestException("GitHub down")):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 502
    data = response.json()
    assert "GitHub API failure" in data["detail"]


def test_review_pr_unexpected_exception():
    """Test /review endpoint raises 500 on unexpected errors."""
    with patch("app.main.review_github_pr", side_effect=Exception("Unexpected error")):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 500
    data = response.json()
    assert "Internal server error" in data["detail"]
    assert "Unexpected error" in data["detail"]


def test_review_diff_returns_merged_actions():
    """Test that review_diff returns merged heuristic + AI actions correctly."""
    from app.review import review_diff

    diff = "+ print('hello world')"

    fake_openai_response = MagicMock()
    fake_openai_response.choices = [
        MagicMock(message=MagicMock(
            content=json.dumps({
                "summary": "Adds logging",
                "issues": ["Missing tests"],
                "complexity_score": 3,
                "risk_level": "low",
                "recommended_actions": ["Add unit tests"]
            })
        ))
    ]

    with patch("app.review.openai.chat.completions.create", return_value=fake_openai_response):
        result = review_diff(diff)

    # Complexity and risk reflect merged heuristic
    assert result["complexity_score"] == 3
    assert result["risk_level"] == "medium"  # heuristic adds medium risk
    expected_actions = set(["Add unit tests", "Manual review recommended"])
    assert set(result["recommended_actions"]) == expected_actions
