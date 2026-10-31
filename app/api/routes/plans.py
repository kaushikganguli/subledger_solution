from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies import service_bundle
from app.schemas.common import PlanCreate, PlanUpdate, PlanOut
router = APIRouter(prefix="/plans", tags=["Plans"])
@router.post("", response_model=PlanOut, status_code=201)
def create_plan(payload: PlanCreate, db: Session = Depends(get_db)): return service_bundle(db)["plans"].create(payload)
@router.get("", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)): return service_bundle(db)["plans"].list()
@router.patch("/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, payload: PlanUpdate, db: Session = Depends(get_db)): return service_bundle(db)["plans"].update(plan_id, payload)
