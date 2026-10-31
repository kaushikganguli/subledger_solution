from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import service_bundle
from app.schemas.common import SubscriptionCreate, SubscriptionOut
router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
@router.post("", response_model=SubscriptionOut, status_code=201)
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)): return service_bundle(db)["subscriptions"].create(payload)
@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(db: Session = Depends(get_db)): return service_bundle(db)["subscriptions"].list()
@router.patch("/{subscription_id}/cancel", response_model=SubscriptionOut)
def cancel_subscription(subscription_id: int, db: Session = Depends(get_db)): return service_bundle(db)["subscriptions"].cancel(subscription_id)
