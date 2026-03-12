"""Webhook Service for Make.com and external integrations"""

import hmac
import hashlib
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import httpx
import structlog

logger = structlog.get_logger()


async def send_webhook(
    url: str,
    event: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
) -> Tuple[bool, int]:
    """Send a webhook to an external URL"""
    
    body = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload,
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SellScope-Webhook/1.0",
    }
    
    if secret:
        import json
        body_str = json.dumps(body, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            body_str.encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-SellScope-Signature"] = f"sha256={signature}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=body,
                headers=headers,
                timeout=30.0,
            )
            
            logger.info(
                "Webhook sent",
                url=url,
                event=event,
                status_code=response.status_code,
            )
            
            return response.status_code < 400, response.status_code
    
    except httpx.TimeoutException:
        logger.error("Webhook timeout", url=url, event=event)
        return False, 408
    
    except httpx.RequestError as e:
        logger.error("Webhook error", url=url, event=event, error=str(e))
        return False, 0


async def trigger_event(
    event: str,
    payload: Dict[str, Any],
    user_id: int,
    db,
) -> None:
    """Trigger webhooks for a specific event"""
    from sqlalchemy import select
    from app.models.automation import Webhook
    
    result = await db.execute(
        select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.is_active == True,
        )
    )
    webhooks = result.scalars().all()
    
    for webhook in webhooks:
        if event in webhook.events:
            success, status_code = await send_webhook(
                url=webhook.url,
                event=event,
                payload=payload,
                secret=webhook.secret,
            )
            
            webhook.last_triggered_at = datetime.utcnow()
            webhook.last_status_code = status_code
            
            if not success:
                webhook.failure_count += 1
            else:
                webhook.failure_count = 0
    
    await db.commit()


def create_make_webhook_payload(
    action: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a Make.com compatible webhook payload"""
    return {
        "action": action,
        "data": data,
        "source": "sellscope",
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_social_post_payload(
    image_url: str,
    caption: str,
    hashtags: list,
    platforms: list,
) -> Dict[str, Any]:
    """Create a payload for social media automation"""
    return {
        "image_url": image_url,
        "caption": caption,
        "hashtags": hashtags,
        "platforms": platforms,
        "schedule": None,
    }
