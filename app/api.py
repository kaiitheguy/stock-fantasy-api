from typing import Any, Dict
import os

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

from .schemas import RationaleRequest
from .services import EnvironmentMissing, OpenAIError, fetch_yahoo_data, generate_rationale


router = APIRouter()


@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    return {"ok": True, "env": bool(os.environ.get("OPENAI_API_KEY"))}


@router.get("/api/yahoo")
async def yahoo(symbol: str, response: Response):
    trimmed = symbol.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail={"error": "Missing symbol"})

    try:
        data = await fetch_yahoo_data(trimmed)
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch stock data", "detail": str(err)},
        ) from err

    response.headers["Cache-Control"] = "no-store"
    return data


@router.post("/api/rationale")
async def rationale(payload: RationaleRequest) -> JSONResponse:
    try:
        result = await generate_rationale(payload)
    except EnvironmentMissing as err:
        return JSONResponse(status_code=500, content=err.detail)
    except OpenAIError as err:
        return JSONResponse(status_code=500, content=err.detail)

    return JSONResponse(result)
