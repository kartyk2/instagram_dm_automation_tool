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
    if not sig_header:
        logger.warning("⚠️ No X-Hub-Signature-256 header present")
        return False

    if not sig_header.startswith("sha256="):
        logger.warning(f"⚠️ Unexpected signature format: {sig_header[:20]}")
        return False

    secret = os.environ["APP_SECRET"].encode()

    # ✅ Fixed: hmac.new → hmac.new is wrong, correct is hmac.new
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    received = sig_header[7:]  # strip "sha256="

    match = hmac.compare_digest(expected, received)
    if not match:
        logger.warning(f"⚠️ Signature mismatch — expected: {expected[:10]}... got: {received[:10]}...")
    return match


@router.get("/webhook")
async def verify(request: Request):
    """Meta calls this once to verify your endpoint."""
    # Read params manually — avoids 422 if any param is missing
    params        = dict(request.query_params)
    mode          = params.get("hub.mode")
    token         = params.get("hub.verify_token")
    challenge     = params.get("hub.challenge")

    logger.info(f"🔍 Verify hit — mode={mode} token_match={token == os.environ['VERIFY_TOKEN']}")

    if mode == "subscribe" and token == os.environ["VERIFY_TOKEN"]:
        logger.info("✅ Webhook verified successfully")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive(request: Request):
    """Meta sends DM events here."""
    body = await request.body()
    sig  = request.headers.get("X-Hub-Signature-256")

    logger.info(f"📥 POST received — size={len(body)} bytes sig_present={bool(sig)}")

    # ✅ Log but don't hard-reject during dev — signature can fail if APP_SECRET is wrong
    if not _verify_signature(body, sig):
        logger.error("❌ Signature verification failed — check APP_SECRET env var")
        # During dev: log and continue instead of rejecting
        # In production: uncomment the line below
        # raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse JSON body: {e}")
        return {"status": "error"}

    logger.info(f"📦 Payload object type: {data.get('object')}")

    if data.get("object") != "instagram":
        logger.info(f"⏭️ Ignoring non-instagram object: {data.get('object')}")
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        logger.info(f"📂 Entry id={entry.get('id')}")

        for event in entry.get("messaging", []):
            sender_igsid = event.get("sender", {}).get("id")
            msg          = event.get("message", {})

            logger.info(f"💬 Event — sender={sender_igsid} keys={list(event.keys())}")

            # Skip echo (your own outgoing messages)
            if msg.get("is_echo"):
                logger.info("⏭️ Skipping echo message")
                continue

            text = msg.get("text")
            if not text:
                logger.info(f"⏭️ No text in message — type keys: {list(msg.keys())}")
                continue

            logger.info(f"📨 DM from {sender_igsid}: {text}")

            reply_text = generate_reply(text)
            try:
                result = await send_reply(sender_igsid, reply_text)
                logger.info(f"✅ Reply sent — {result}")
            except Exception as e:
                logger.error(f"❌ Failed to send reply: {e}")

    return {"status": "ok"}


def generate_reply(incoming_text: str) -> str:
    return f"Thanks for your message! You said: {incoming_text}"