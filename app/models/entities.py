from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Numeric, Text, UniqueConstraint, Index, event
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from app.db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    company_name: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="customer")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="customer")

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscription_customer_plan_status", "customer_id", "plan_id", "status"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    customer: Mapped[Customer] = relationship(back_populates="subscriptions")
    plan: Mapped[Plan] = relationship(back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="subscription")

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="issued")
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    subscription: Mapped[Subscription] = relationship(back_populates="invoices")
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="invoice")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="invoice")

class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_reference: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    invoice: Mapped[Invoice] = relationship(back_populates="payment_attempts")

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    entry_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    customer: Mapped[Customer] = relationship(back_populates="ledger_entries")
    invoice: Mapped[Invoice | None] = relationship(back_populates="ledger_entries")

# Protect append-only ledger records from accidental ORM mutation/deletion.
@event.listens_for(Session, "before_flush")
def _ledger_is_append_only(session, flush_context, instances):
    for obj in session.deleted:
        if isinstance(obj, LedgerEntry):
            raise ValueError("Ledger entries are append-only and cannot be deleted")
    for obj in session.dirty:
        if isinstance(obj, LedgerEntry) and session.is_modified(obj, include_collections=False):
            raise ValueError("Ledger entries are append-only and cannot be modified")
