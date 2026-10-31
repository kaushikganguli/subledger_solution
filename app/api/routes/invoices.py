from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import service_bundle
from app.schemas.common import InvoiceGenerate, InvoiceOut
router = APIRouter(prefix="/invoices", tags=["Invoices"])
@router.post("/generate", response_model=InvoiceOut, status_code=201)
def generate_invoice(payload: InvoiceGenerate, db: Session = Depends(get_db)): return service_bundle(db)["invoices"].generate(payload)
@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)): return service_bundle(db)["invoices"].get(invoice_id)
