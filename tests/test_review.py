# tests/test_review.py
import json
import pytest
from unittest.mock import patch, MagicMock
import os
from openai import OpenAIError
from app.review import review_diff, AIReview

# Sample diffs
SAMPLE_DIFF = """
diff --git a/example.py b/example.py
index 123abc..456def 100644
--- a/example.py
+++ b/example.py
@@ -1 +1,2 @@
-print("Hello world")
+print("Hello, world!")
+print("Another line")
"""

os.environ["OPENAI_API_KEY"] = "test"  # Prevent OpenAIError

LARGE_DIFF = "\n".join(f"+ line {i}" for i in range(300))

def make_fake_response(content_dict):
    """Helper to build a fake OpenAI response."""
    fake_response = MagicMock()
    fake_response.choices = [
        MagicMock(message=MagicMock(content=json.dumps(content_dict)))
    ]
    return fake_response


@patch("app.review.openai.chat.completions.create")
def test_review_diff_success(mock_create):
    """AI succeeds; result merges AI + heuristic outputs."""
    fake_create_response = make_fake_response({
        "summary": "Adds logging",
        "issues": ["Missing tests"],
        "complexity_score": 3,
        "risk_level": "low",
        "recommended_actions": ["Add unit tests"]
    })
    mock_create.return_value = fake_create_response

    result = review_diff(SAMPLE_DIFF)

    # AI summary
    assert result["summary"] == "Adds logging"

    # Issues include AI + heuristic
    assert "Missing tests" in result["issues"]
    assert "Debug prints detected" in result["issues"]

    # Risk should be at least medium due to debug prints
    assert result["risk_level"] == "medium"

    # Recommended actions include heuristic
    assert "Manual review recommended" in result["recommended_actions"]

    # Lines in diff
    assert result["lines_in_diff"] == len(SAMPLE_DIFF.splitlines())


@patch("app.review.openai.chat.completions.create")
def test_review_diff_openai_error(mock_create):
    """AI fails; fallback to heuristic review."""
    mock_create.side_effect = OpenAIError("Rate limit exceeded")

    result = review_diff(SAMPLE_DIFF)

    # Summary falls back to heuristic
    assert result["summary"] == "Heuristic pre-review"

    # Heuristic issues detected
    assert "Debug prints detected" in result["issues"]

    # Risk at least medium due to debug prints
    assert result["risk_level"] == "medium"

    # Recommended actions include heuristic
    assert "Manual review recommended" in result["recommended_actions"]

    # Lines in diff
    assert result["lines_in_diff"] == len(SAMPLE_DIFF.splitlines())


@patch("app.review.openai.chat.completions.create")
def test_review_diff_large_pr_risk(mock_create):
    """Large PR (>200 lines) triggers high-risk heuristic."""
    fake_create_response = make_fake_response({
        "summary": "Adds many lines",
        "issues": ["Needs careful review"],
        "complexity_score": 5,
        "risk_level": "medium",
        "recommended_actions": ["Add unit tests"]
    })
    mock_create.return_value = fake_create_response

    result = review_diff(LARGE_DIFF)

    # Summary matches AI
    assert result["summary"] == "Adds many lines"

    # Risk should be upgraded to high for large PR
    assert result["risk_level"] == "high"

    # Recommended actions include heuristic
    assert "Manual review recommended" in result["recommended_actions"]

    # Lines in diff
    assert result["lines_in_diff"] == len(LARGE_DIFF.splitlines())


@patch("app.review.openai.chat.completions.create")
def test_review_diff_todo_detection(mock_create):
    """Heuristic detects TODO/FIXME comments in diff."""
    diff_with_todo = "+ # TODO: fix this\n+print('hello')"
    fake_create_response = make_fake_response({
        "summary": "Adds TODO",
        "issues": [],
        "complexity_score": 2,
        "risk_level": "low",
        "recommended_actions": []
    })
    mock_create.return_value = fake_create_response

    result = review_diff(diff_with_todo)

    # Heuristic issues
    assert "Contains TODO/FIXME comments" in result["issues"]
    assert "Debug prints detected" in result["issues"]

    # Recommended actions include heuristic
    assert "Manual review recommended" in result["recommended_actions"]

    # Lines in diff
    assert result["lines_in_diff"] == len(diff_with_todo.splitlines())
