# AI PR Reviewer

## Setup
1. Clone repo
2. Create virtual environment: python3 -m venv venv
3. Activate: source venv/bin/activate
4. Install dependencies: pip install -r requirements.txt
5. Add `.env` with OPENAI_API_KEY and GITHUB_TOKEN
6. Run server: uvicorn app.main:app --reload

## Example Request
curl -X POST http://127.0.0.1:8000/review \
-H "Content-Type: application/json" \
-d '{"owner":"XXXX","repo":"XXXX","pr_number":108}'
