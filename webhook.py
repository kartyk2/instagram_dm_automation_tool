import logging
import hmac
import hashlib
import os
from fastapi import APIRouter, Request, Response, HTTPException, Query
from messenger import send_reply

router = APIRouter()
logger = logging.getLogger(__name__)


def _verify_signature(body: bytes, sig_header: str | None) -> bool:
    """Verify the request genuinely came from Meta."""
    if not sig_header or not sig_header.startswith("sha256="):
        return False
    secret = os.environ["APP_SECRET"].encode()
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header[7:])


@router.get("/webhook")
async def verify(
    hub_mode: str       = Query(alias="hub.mode"),
    hub_challenge: str  = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    """Meta calls this once to verify your endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == os.environ["VERIFY_TOKEN"]:
        logger.info("✅ Webhook verified")
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive(request: Request):
    """Meta sends DM events here."""
    body = await request.body()

    # Verify the payload is from Meta
    if not _verify_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    if data.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):

            sender_igsid = event["sender"]["id"]     # ← who sent the DM
            # event["recipient"]["id"] is YOUR IG account — don't use this as recipient

            msg = event.get("message", {})

            # Skip echo events (your own sent messages)
            if msg.get("is_echo"):
                continue

            text = msg.get("text")
            if not text:
                continue  # ignore stickers, reacts, etc. for now

            logger.info(f"📨 DM from {sender_igsid}: {text}")

            # Your auto-reply logic here
            reply_text = generate_reply(text)
            await send_reply(sender_igsid, reply_text)

    return {"status": "ok"}


def generate_reply(incoming_text: str) -> str:
    """Swap this out for AI, keyword matching, whatever you want."""
    return f"Thanks for your message! You said: {incoming_text}"