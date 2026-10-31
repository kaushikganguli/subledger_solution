from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Plan, Customer, Subscription, Invoice, PaymentAttempt, LedgerEntry

class BaseRepository:
    def __init__(self, db: Session): self.db = db

class PlanRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj
    def get(self, ident): return self.db.get(Plan, ident)
    def list(self): return list(self.db.scalars(select(Plan).order_by(Plan.id.desc())))

class CustomerRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj
    def get(self, ident): return self.db.get(Customer, ident)
    def list(self): return list(self.db.scalars(select(Customer).order_by(Customer.id.desc())))
    def by_email(self, email): return self.db.scalar(select(Customer).where(Customer.email == email))

class SubscriptionRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj
    def get(self, ident): return self.db.get(Subscription, ident)
    def list(self): return list(self.db.scalars(select(Subscription).order_by(Subscription.id.desc())))
    def active_for_customer_plan(self, customer_id, plan_id):
        return self.db.scalar(select(Subscription).where(Subscription.customer_id == customer_id, Subscription.plan_id == plan_id, Subscription.status == "active"))

class InvoiceRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj
    def get(self, ident): return self.db.get(Invoice, ident)

class PaymentAttemptRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj

class LedgerRepository(BaseRepository):
    def create(self, obj): self.db.add(obj); self.db.flush(); return obj
    def for_customer(self, customer_id): return list(self.db.scalars(select(LedgerEntry).where(LedgerEntry.customer_id == customer_id).order_by(LedgerEntry.created_at.desc(), LedgerEntry.id.desc())))
