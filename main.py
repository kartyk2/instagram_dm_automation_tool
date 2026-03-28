import os
import uvicorn
from fastapi import FastAPI
from webhook import router as webhook_router

app = FastAPI(title="Instagram AutoDM")

app.include_router(webhook_router)


@app.get("/")
def health():
    return {"status": "Instagram AutoDM is running ✅"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
