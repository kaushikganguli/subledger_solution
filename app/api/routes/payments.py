from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import service_bundle
from app.schemas.common import PaymentCreate, PaymentResult
router = APIRouter(prefix="/payments", tags=["Payments"])
@router.post("/record", response_model=PaymentResult, status_code=201)
def record_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    attempt, invoice = service_bundle(db)["payments"].record(payload)
    return {"payment_attempt": attempt, "invoice": invoice}
