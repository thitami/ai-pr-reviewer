# tests/test_review.py

import warnings
import pytest
from unittest.mock import patch, MagicMock

# Suppress urllib3 NotOpenSSLWarning in tests
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

from app.review import review_diff

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

def test_review_diff_success():
    """Test that review_diff returns expected structure on successful OpenAI call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Summary line\nIssue 1\nIssue 2"

    with patch("app.review.openai.chat.completions.create", return_value=mock_response):
        result = review_diff(SAMPLE_DIFF)

    assert "summary" in result
    assert "issues" in result
    assert "lines_in_diff" in result
    assert result["summary"] == "Summary line"
    assert result["issues"] == ["Issue 1", "Issue 2"]
    assert result["lines_in_diff"] == len(SAMPLE_DIFF.splitlines())

def test_review_diff_openai_error():
    """Test that review_diff handles OpenAI errors gracefully."""
    from openai import OpenAIError

    with patch("app.review.openai.chat.completions.create") as mock_create:
        mock_create.side_effect = OpenAIError("Rate limit exceeded")
        result = review_diff(SAMPLE_DIFF)

    assert result["summary"] == ""
    assert result["issues"] == []
    assert result["lines_in_diff"] == len(SAMPLE_DIFF.splitlines())
    assert "error" in result
    assert "Rate limit exceeded" in result["error"]
