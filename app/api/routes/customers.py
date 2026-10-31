from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import service_bundle
from app.schemas.common import CustomerCreate, CustomerOut
router = APIRouter(prefix="/customers", tags=["Customers"])
@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)): return service_bundle(db)["customers"].create(payload)
@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)): return service_bundle(db)["customers"].list()
@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)): return service_bundle(db)["customers"].get(customer_id)
@router.get("/{customer_id}/ledger", tags=["Ledger"])
def get_customer_ledger(customer_id: int, db: Session = Depends(get_db)): return service_bundle(db)["ledger"].customer_history(customer_id)
