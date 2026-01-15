# tests/test_main.py

import pytest, json
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.review import review_diff

from app.main import app

client = TestClient(app)

# Sample request payload
sample_payload = {
    "owner": "thitami",
    "repo": "ai-pr-reviewer",
    "pr_number": 1
}

# Mocked response from review_github_pr
mock_review_text = "This is a mocked AI review of the PR."

def test_review_pr_success():
    """Test /review endpoint returns expected structure on success."""
    with patch("app.main.review_github_pr", return_value=mock_review_text):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysis"] == mock_review_text
    assert data["pr"]["owner"] == sample_payload["owner"]
    assert data["pr"]["repo"] == sample_payload["repo"]
    assert data["pr"]["pr_number"] == sample_payload["pr_number"]

def test_review_pr_exception():
    """Test /review endpoint handles exceptions gracefully."""
    with patch("app.main.review_github_pr", side_effect=Exception("Something went wrong")):
        response = client.post("/review", json=sample_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Something went wrong" in data["error"]

def test_review_diff_returns_structured_data():
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

    assert result["complexity_score"] == 3
    assert result["risk_level"] == "low"
    assert result["recommended_actions"] == ["Add unit tests"]
