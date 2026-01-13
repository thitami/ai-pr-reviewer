from fastapi import FastAPI
from app.review import review_diff

app = FastAPI()

@app.post("/review")
async def review(payload: dict):
    diff = payload.get("diff", "")
    result = review_diff(diff)
    return {"review": result}
