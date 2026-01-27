# AI PR Reviewer

An intelligent code review assistant that combines AI analysis with heuristic checks to provide comprehensive feedback on GitHub pull requests.

## Features

- **AI-Powered Analysis**: Leverages OpenAI's GPT-4 to analyze code changes
- **Heuristic Checks**: Detects common issues like debug prints, TODO comments, and large PRs
- **Risk Assessment**: Automatically evaluates PR risk level (low/medium/high)
- **Structured Output**: Returns detailed JSON responses with actionable insights
- **Fallback Mechanism**: Continues with heuristic analysis if AI service is unavailable

## Architecture

The project consists of three main components:

- **`app/main.py`**: FastAPI application with the `/review` endpoint
- **`app/review.py`**: Core review logic combining AI and heuristic analysis
- **`tests/`**: Comprehensive test suite using pytest

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- GitHub access (optional: personal access token for private repos)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-pr-reviewer
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here  # Optional, for private repos
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://127.0.0.1:8000`

## Usage

### API Endpoint

**POST** `/review`

Review a GitHub pull request and receive structured analysis.

#### Request Body

```json
{
  "owner": "github-username",
  "repo": "repository-name",
  "pr_number": 123
}
```

#### Response

```json
{
  "success": true,
  "analysis": {
    "summary": "Brief description of changes",
    "issues": [
      "Debug prints detected",
      "Missing tests"
    ],
    "complexity_score": 3,
    "risk_level": "medium",
    "recommended_actions": [
      "Add unit tests",
      "Manual review recommended"
    ],
    "lines_in_diff": 42,
    "error": ""
  },
  "pr": {
    "owner": "github-username",
    "repo": "repository-name",
    "pr_number": 123
  }
}
```

### Example Requests

#### Using cURL

```bash
curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "thitami",
    "repo": "ai-pr-reviewer",
    "pr_number": 1
  }'
```

#### Using Python

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/review",
    json={
        "owner": "thitami",
        "repo": "ai-pr-reviewer",
        "pr_number": 1
    }
)

print(response.json())
```

#### Using JavaScript

```javascript
fetch('http://127.0.0.1:8000/review', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    owner: 'thitami',
    repo: 'ai-pr-reviewer',
    pr_number: 1
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Review Logic

### AI Analysis

The system uses OpenAI's GPT-4 to:
- Summarize code changes
- Identify potential issues
- Assess complexity (0-10 scale)
- Suggest recommended actions

### Heuristic Checks

Automatic detection of:
- **Debug prints**: Identifies `print()` statements in code
- **TODO/FIXME comments**: Flags incomplete work
- **Large PRs**: PRs with >200 lines automatically marked as high-risk

### Risk Levels

- **Low**: Simple changes with no detected issues
- **Medium**: Contains debug prints, TODOs, or minor concerns
- **High**: Large PRs (>200 lines) or multiple risk factors

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

View coverage report:

```bash
open htmlcov/index.html
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Error Handling

The API handles various error scenarios:

- **GitHub API Failures**: Returns 502 Bad Gateway
- **AI Service Unavailable**: Falls back to heuristic analysis only
- **Invalid Input**: Returns 422 Unprocessable Entity with validation errors
- **Unexpected Errors**: Returns 500 Internal Server Error

## Project Structure

```
ai-pr-reviewer/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   └── review.py        # Review logic (AI + heuristics)
├── tests/
│   ├── __init__.py
│   ├── test_main.py     # API endpoint tests
│   └── test_review.py   # Review logic tests
├── .env                 # Environment variables (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## Dependencies

Key dependencies:
- **FastAPI**: Modern web framework
- **OpenAI**: AI-powered code analysis
- **Pydantic**: Data validation and settings management
- **Requests**: HTTP library for GitHub API
- **pytest**: Testing framework

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Roadmap

Future enhancements:
- Support for GitLab and Bitbucket
- Custom heuristic rule configuration
- Integration with CI/CD pipelines
- Historical analysis and trend tracking
- Multi-language support
- Webhook support for automatic reviews