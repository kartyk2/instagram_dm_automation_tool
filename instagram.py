import os
import logging
import httpx

logger = logging.getLogger(__name__)

API_VERSION = "v21.0"
GRAPH_URL   = f"https://graph.facebook.com/{API_VERSION}/me/messages"


async def send_reply(recipient_id: str, text: str) -> dict:
    """
    Sends a text reply to a user via the Instagram Messaging API.

    Args:
        recipient_id: The sender's Instagram-scoped user ID
        text:         The reply message text
    """
    token = os.environ["IG_ACCESS_TOKEN"]

    payload = {
        "recipient": {"id": recipient_id},
        "message":   {"text": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GRAPH_URL,
            params={"access_token": token},
            json=payload,
            timeout=10.0,
        )

    if response.status_code != 200:
        logger.error(f"❌ Instagram API error {response.status_code}: {response.text}")
        response.raise_for_status()

    return response.json()
