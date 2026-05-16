import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()  # must be before any os.environ access

from fastapi import FastAPI
from webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate env vars at startup — fail loud, fail early
    import os
    required = ["APP_ID", "APP_SECRET", "VERIFY_TOKEN", "IG_ACCESS_TOKEN", "IG_USER_ID"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(webhook_router)