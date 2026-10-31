from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|quarterly|yearly)$")
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)

class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    billing_cycle: str | None = Field(default=None, pattern="^(monthly|quarterly|yearly)$")
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")

class PlanOut(ORMModel):
    id: int; name: str; description: str | None; billing_cycle: str; price: Decimal; currency: str; status: str; created_at: datetime; updated_at: datetime

class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: EmailStr
    company_name: str | None = None

class CustomerOut(ORMModel):
    id: int; name: str; email: EmailStr; company_name: str | None; status: str; created_at: datetime

class SubscriptionCreate(BaseModel):
    customer_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)

class SubscriptionOut(ORMModel):
    id: int; customer_id: int; plan_id: int; status: str; start_date: datetime; current_period_start: datetime; current_period_end: datetime; canceled_at: datetime | None

class InvoiceGenerate(BaseModel):
    subscription_id: int = Field(gt=0)
    period_start: datetime | None = None
    period_end: datetime | None = None

class InvoiceOut(ORMModel):
    id: int; subscription_id: int; customer_id: int; amount_due: Decimal; amount_paid: Decimal; currency: str; status: str; period_start: datetime; period_end: datetime; due_date: datetime | None; created_at: datetime

class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    status: str = Field(pattern="^(success|failed)$")
    provider_reference: str = Field(min_length=1, max_length=120)
    failure_reason: str | None = None

class PaymentOut(ORMModel):
    id: int; invoice_id: int; amount: Decimal; currency: str; status: str; provider_reference: str; failure_reason: str | None; created_at: datetime

class PaymentResult(BaseModel):
    payment_attempt: PaymentOut
    invoice: InvoiceOut

class LedgerOut(ORMModel):
    id: int; customer_id: int; invoice_id: int | None; entry_type: str; amount: Decimal; currency: str; reference_id: str; description: str | None; created_at: datetime
