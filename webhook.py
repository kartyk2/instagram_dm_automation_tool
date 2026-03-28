import os
import logging
from fastapi import APIRouter, Request, Response, HTTPException
from matcher import match_reply
from instagram import send_reply

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Webhook verification (one-time Meta setup) ────────────────
@router.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == os.environ["WEBHOOK_VERIFY_TOKEN"]:
        logger.info("✅ Webhook verified by Meta")
        return Response(content=challenge, media_type="text/plain")

    logger.warning("❌ Webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Incoming DM events ────────────────────────────────────────
@router.post("/webhook")
async def handle_webhook(request: Request):
    # Always return 200 immediately so Meta doesn't retry
    body = await request.json()
    print(f" RAW: {body}")


    if body.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in body.get("entry", []):
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id")
            my_id     = event.get("recipient", {}).get("id")
            message   = event.get("message", {})
            text      = message.get("text")

            # Skip echoed outgoing messages or non-text events
            if not text or sender_id == my_id:
                continue

            logger.info(f"📩 DM from {sender_id}: \"{text}\"")

            reply = match_reply(text)

            if reply:
                logger.info(f"💬 Replying: \"{reply}\"")
                await send_reply(sender_id, reply)
            else:
                logger.info("⏭️  No rule matched, skipping.")

    return {"status": "ok"}
