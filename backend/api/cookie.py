# api/cookie.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.shared import CookiePayload
from services.cookie import encode

router = APIRouter(tags=["cookie"])


@router.post("/set-cookie")
def set_cookie(data: CookiePayload):
    if not data.user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    response = JSONResponse({"message": "cookie set"})
    response.set_cookie(
        key="sinatra_user_id",
        value=encode(data.user_id),
        httponly=True,
        secure=True,
        samesite="None",
        path="/",
        max_age=3600 * 24 * 7,  # 7 days
    )
    return response
