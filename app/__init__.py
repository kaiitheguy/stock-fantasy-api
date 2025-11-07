import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .api.trading_api import router as trading_router


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("[REQ] %s %s", request.method, request.url.path)
    return await call_next(request)


@app.on_event("startup")
async def log_env_state():
    logger.info("OPENAI key configured: %s", bool(os.environ.get("OPENAI_API_KEY")))


app.include_router(trading_router)
