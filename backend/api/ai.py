# api/ai.py
import json
import os

from fastapi import APIRouter, HTTPException, Query
from openai import OpenAI

from db.mongo import users_collection

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None
    print("⚠️ WARNING: OPENAI_API_KEY not set. /ai-genres route will be unavailable.")

router = APIRouter(tags=["ai"])


def chatgpt(prompt: str, model: str = "gpt-4.1-nano") -> str:
    if not client:
        raise HTTPException(
            status_code=503, detail="AI service unavailable: OPENAI_API_KEY not set"
        )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(model=model, messages=messages, temperature=0.5)
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")


@router.get("/ai-genres")
def generate_ai_genre_commentary(user_id: str = Query(...)):
    if not client:
        raise HTTPException(
            status_code=503, detail="AI service unavailable: OPENAI_API_KEY not set"
        )

    doc = users_collection.find_one({"user_id": user_id})
    if not doc or "genre_analysis" not in doc:
        raise HTTPException(status_code=404, detail="No genre analysis found for user")

    music_data = doc["genre_analysis"]
    music_data_str = json.dumps(music_data)

    prompt = f"""
Your task is to write two witty sentences about the /
user's music data. Your results will appear on an app that /
examines their music taste. The user's music data is /
delimited by three backticks.

Step 1: Write one short sentence about their vibe.
Step 2: In one sentence, write a roast about the user's top sub-genre with insider reference.

Limit each sentence to 10 words maximum.

Avoid using the words "genre" and "sub-genre".

Frame your response to be directed to the user.

Format your results as a JSON object with "sen-#" and /
"line" as keys.

```{music_data_str}```
"""

    result = chatgpt(prompt)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="OpenAI response was not valid JSON")

    return {"result": parsed}
