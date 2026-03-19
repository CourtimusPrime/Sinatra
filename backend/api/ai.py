# api/ai.py
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Query
from openai import OpenAI

from db import queries as q

logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None
    logger.warning("OPENAI_API_KEY not set. /ai-genres route will be unavailable.")

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
    except Exception:
        raise HTTPException(status_code=500, detail="AI service error")


@router.get("/ai-genres")
def generate_ai_genre_commentary(user_id: str = Query(...)):
    if not client:
        raise HTTPException(
            status_code=503, detail="AI service unavailable: OPENAI_API_KEY not set"
        )

    music_data = q.get_genre_analysis(user_id)
    if not music_data:
        raise HTTPException(status_code=404, detail="No genre analysis found for user")

    safe_data = {
        "sub_genres": {k: v for k, v in list(music_data.get("sub_genres", {}).items())[:10]},
        "meta_genres": {k: v for k, v in list(music_data.get("meta_genres", {}).items())[:10]},
        "top_subgenre": music_data.get("top_subgenre", {}),
    }
    music_data_str = json.dumps(safe_data)[:2000]

    prompt = f"""
Your task is to write two witty sentences about the \
user's music data. Your results will appear on an app that \
examines their music taste. The user's music data is \
provided below as JSON.

Step 1: Write one short sentence about their vibe.
Step 2: In one sentence, write a roast about the user's top sub-genre with insider reference.

Limit each sentence to 10 words maximum.

Avoid using the words "genre" and "sub-genre".

Frame your response to be directed to the user.

Format your results as a JSON object with "sen-#" and \
"line" as keys.

{music_data_str}
"""

    result = chatgpt(prompt)

    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="OpenAI response was not valid JSON")

    return {"result": parsed}
