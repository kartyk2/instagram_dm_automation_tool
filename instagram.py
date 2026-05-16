import os
import logging
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

API_VERSION = "v25.0"


@lru_cache(maxsize=1)
def _get_config() -> tuple[str, str, str]:
    """
    Load and validate required env vars once at startup.
    Returns (token, page_id, graph_url)
    """
    token   = os.environ.get("IG_ACCESS_TOKEN", "")
    page_id = os.environ.get("IG_PAGE_ID", "")       # needed for FB Login path

    if not token:
        raise RuntimeError("IG_ACCESS_TOKEN env var is not set")
    if not page_id:
        raise RuntimeError("IG_PAGE_ID env var is not set")

    # --- Choose ONE of these based on your auth path ---
    # Facebook Login path  →  Page Access Token + graph.facebook.com
    # graph_url = f"https://graph.facebook.com/{API_VERSION}/{page_id}/messages"

    # Instagram Login path →  IG User Access Token + graph.instagram.com
    graph_url = f"https://graph.instagram.com/{API_VERSION}/me/messages"

    return token, page_id, graph_url


async def send_reply(
    recipient_igsid: str,   # renamed: makes clear this must be the IGSID from sender.id
    text: str,
    *,
    max_retries: int = 2,
) -> dict:
    """
    Sends a text reply to a user via the Instagram Messaging API.

    Args:
        recipient_igsid: The IGSID from webhook's entry[0].messaging[0].sender.id
        text:            The reply message text (max 1000 bytes, UTF-8)
    """
    if not recipient_igsid:
        raise ValueError("recipient_igsid must not be empty")
    if not text or len(text.encode()) > 1000:
        raise ValueError("text must be non-empty and ≤ 1000 bytes")

    token, _, graph_url = _get_config()

    payload = {
        "recipient": {"id": recipient_igsid},
        "message":   {"text": text},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    last_exc: Exception | None = None

    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(graph_url, headers=headers, json=payload)

                # Retryable: rate-limit or transient server error
                if response.status_code in (429, 500, 502, 503):
                    logger.warning(
                        f"Retryable error on attempt {attempt + 1}: "
                        f"{response.status_code} {response.text}"
                    )
                    if attempt < max_retries:
                        continue

                # Auth / bad request errors — no point retrying
                if response.status_code == 401:
                    logger.error("❌ Token invalid or expired — refresh IG_ACCESS_TOKEN")
                    response.raise_for_status()

                if response.status_code == 400:
                    body = response.json()
                    logger.error(f"❌ Bad request: {body}")
                    # Surface the Meta error code for easier debugging
                    raise ValueError(
                        f"Meta API 400: {body.get('error', {}).get('message', response.text)}"
                    )

                response.raise_for_status()

                data = response.json()
                logger.info(f"✅ Reply sent — message_id: {data.get('message_id')}")
                return data

            except httpx.TimeoutException as exc:
                last_exc = exc
                logger.warning(f"Timeout on attempt {attempt + 1}")

    raise RuntimeError(f"Failed to send reply after {max_retries + 1} attempts") from last_exc