"""Webhooks router for Make.com and external integrations"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.automation import Webhook, WebhookEvent

router = APIRouter()


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str]
    secret: Optional[str] = None


class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: List[str]
    is_active: bool
    last_triggered_at: Optional[datetime]
    failure_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookTest(BaseModel):
    event: str
    payload: dict


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_events = [e.value for e in WebhookEvent]
    for event in webhook_data.events:
        if event not in valid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event: {event}. Valid events: {valid_events}",
            )
    
    webhook = Webhook(
        user_id=int(current_user["user_id"]),
        name=webhook_data.name,
        url=webhook_data.url,
        events=webhook_data.events,
        secret=webhook_data.secret,
    )
    
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    
    return webhook


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(Webhook.user_id == int(current_user["user_id"]))
    )
    return result.scalars().all()


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == int(current_user["user_id"]),
        )
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == int(current_user["user_id"]),
        )
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook.name = webhook_data.name
    webhook.url = webhook_data.url
    webhook.events = webhook_data.events
    if webhook_data.secret:
        webhook.secret = webhook_data.secret
    
    await db.commit()
    await db.refresh(webhook)
    
    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == int(current_user["user_id"]),
        )
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    await db.delete(webhook)
    await db.commit()
    
    return {"status": "deleted"}


@router.post("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == int(current_user["user_id"]),
        )
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    webhook.is_active = not webhook.is_active
    await db.commit()
    
    return {"is_active": webhook.is_active}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    test_data: WebhookTest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == int(current_user["user_id"]),
        )
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    from app.services.webhook_service import send_webhook
    
    success, status_code = await send_webhook(
        url=webhook.url,
        event=test_data.event,
        payload=test_data.payload,
        secret=webhook.secret,
    )
    
    return {"success": success, "status_code": status_code}


@router.post("/incoming/make")
async def make_webhook_receiver(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    
    action = body.get("action")
    data = body.get("data", {})
    
    if action == "analyze_keyword":
        from app.services.opportunity_engine import calculate_opportunity_score
        score = await calculate_opportunity_score(
            keyword=data.get("keyword"),
            db=db,
        )
        return {"status": "success", "score": score.overall_score}
    
    elif action == "generate_brief":
        from app.services.brief_generator import generate_production_brief
        brief = await generate_production_brief(
            keyword=data.get("keyword"),
            db=db,
        )
        return {"status": "success", "brief": brief}
    
    elif action == "scrape_portfolio":
        from app.models.scrape import ScrapeJob, ScrapeJobType
        job = ScrapeJob(
            job_type=ScrapeJobType.PORTFOLIO,
            target=data.get("contributor_id"),
        )
        db.add(job)
        await db.commit()
        return {"status": "queued", "job_id": job.id}
    
    return {"status": "unknown_action"}
