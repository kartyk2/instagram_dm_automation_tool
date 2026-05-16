import os
import logging
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)
API_VERSION = "v25.0"


@lru_cache(maxsize=1)
def _cfg() -> dict:
    token   = os.environ["IG_ACCESS_TOKEN"]
    user_id = os.environ["IG_USER_ID"]
    if not token or not user_id:
        raise RuntimeError("IG_ACCESS_TOKEN or IG_USER_ID not set")
    return {
        "token": token,
        "url": f"https://graph.instagram.com/{API_VERSION}/{user_id}/messages",
    }


async def send_reply(recipient_igsid: str, text: str) -> dict:
    """
    Reply to a DM. recipient_igsid comes from
    webhook payload: entry[0].messaging[0].sender.id
    """
    if not recipient_igsid:
        raise ValueError("recipient_igsid is empty")
    if not text or len(text.encode()) > 1000:
        raise ValueError("text must be non-empty and ≤ 1000 bytes")

    cfg = _cfg()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            r = await client.post(
                cfg["url"],
                headers={
                    "Authorization": f"Bearer {cfg['token']}",
                    "Content-Type": "application/json",
                },
                json={
                    "recipient": {"id": recipient_igsid},
                    "message":   {"text": text},
                },
            )

            if r.status_code in (429, 500, 502, 503):
                logger.warning(f"Attempt {attempt + 1} failed: {r.status_code}")
                if attempt < 2:
                    continue

            if r.status_code == 400:
                raise ValueError(f"Meta 400: {r.json().get('error', {}).get('message')}")

            if r.status_code == 401:
                raise RuntimeError("Token invalid or expired — refresh IG_ACCESS_TOKEN")

            r.raise_for_status()
            data = r.json()
            logger.info(f"✅ Sent — message_id: {data.get('message_id')}")
            return data

    raise RuntimeError("Failed after 3 attempts")