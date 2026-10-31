from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from app.core.errors import DomainError
from app.models import Plan, Customer, Subscription, Invoice, PaymentAttempt, LedgerEntry

class ServiceBase:
    def __init__(self, db, repos): self.db, self.repos = db, repos
    def commit(self, obj):
        try: self.db.commit(); self.db.refresh(obj); return obj
        except IntegrityError:
            self.db.rollback(); raise DomainError("A uniqueness or database constraint was violated", 409)

class PlanService(ServiceBase):
    def create(self, data):
        if data.price <= 0: raise DomainError("Plan price must be greater than 0")
        return self.commit(self.repos.plans.create(Plan(**{**data.model_dump(), "currency": data.currency.upper()})))
    def list(self): return self.repos.plans.list()
    def update(self, ident, data):
        p = self.repos.plans.get(ident)
        if not p: raise DomainError("Plan not found", 404)
        for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v.upper() if k == "currency" and v else v)
        return self.commit(p)

class CustomerService(ServiceBase):
    def create(self, data):
        payload = data.model_dump(); payload["email"] = str(data.email).lower()
        if self.repos.customers.by_email(payload["email"]): raise DomainError("Customer email already exists", 409)
        return self.commit(self.repos.customers.create(Customer(**payload)))
    def list(self): return self.repos.customers.list()
    def get(self, ident):
        obj = self.repos.customers.get(ident)
        if not obj: raise DomainError("Customer not found", 404)
        return obj

class SubscriptionService(ServiceBase):
    def create(self, data):
        customer = self.repos.customers.get(data.customer_id)
        if not customer or customer.status != "active": raise DomainError("Active customer not found", 404)
        plan = self.repos.plans.get(data.plan_id)
        if not plan or plan.status != "active": raise DomainError("An active plan is required", 400)
        if self.repos.subscriptions.active_for_customer_plan(data.customer_id, data.plan_id): raise DomainError("Customer already has an active subscription to this plan", 409)
        start = datetime.now(timezone.utc)
        days = {"monthly": 30, "quarterly": 90, "yearly": 365}[plan.billing_cycle]
        obj = Subscription(customer_id=data.customer_id, plan_id=data.plan_id, status="active", start_date=start, current_period_start=start, current_period_end=start + timedelta(days=days))
        return self.commit(self.repos.subscriptions.create(obj))
    def list(self): return self.repos.subscriptions.list()
    def cancel(self, ident):
        obj = self.repos.subscriptions.get(ident)
        if not obj: raise DomainError("Subscription not found", 404)
        if obj.status != "active": raise DomainError("Only active subscriptions can be canceled", 409)
        obj.status, obj.canceled_at = "canceled", datetime.now(timezone.utc)
        return self.commit(obj)

class LedgerService(ServiceBase):
    def add(self, customer_id, invoice_id, entry_type, amount, currency, reference_id, description):
        return self.repos.ledger.create(LedgerEntry(customer_id=customer_id, invoice_id=invoice_id, entry_type=entry_type, amount=amount, currency=currency, reference_id=reference_id, description=description))
    def customer_history(self, customer_id):
        if not self.repos.customers.get(customer_id): raise DomainError("Customer not found", 404)
        return self.repos.ledger.for_customer(customer_id)

class InvoiceService(ServiceBase):
    def generate(self, data):
        sub = self.repos.subscriptions.get(data.subscription_id)
        if not sub or sub.status != "active": raise DomainError("An active subscription is required", 400)
        plan = self.repos.plans.get(sub.plan_id)
        start = data.period_start or sub.current_period_start
        end = data.period_end or sub.current_period_end
        if end <= start: raise DomainError("period_end must be later than period_start")
        invoice = Invoice(subscription_id=sub.id, customer_id=sub.customer_id, amount_due=plan.price, amount_paid=Decimal("0.00"), currency=plan.currency, status="issued", period_start=start, period_end=end, due_date=end)
        self.repos.invoices.create(invoice)
        self.repos.ledger.create(LedgerEntry(customer_id=sub.customer_id, invoice=invoice, entry_type="invoice_created", amount=plan.price, currency=plan.currency, reference_id=f"invoice:{invoice.id}", description="Invoice issued"))
        return self.commit(invoice)
    def get(self, ident):
        obj = self.repos.invoices.get(ident)
        if not obj: raise DomainError("Invoice not found", 404)
        return obj

class PaymentService(ServiceBase):
    def record(self, data):
        invoice = self.repos.invoices.get(data.invoice_id)
        if not invoice: raise DomainError("Invoice not found", 404)
        if data.currency.upper() != invoice.currency.upper(): raise DomainError("Payment currency must match invoice currency")
        if invoice.status in ("paid", "void"): raise DomainError("Invoice is not payable", 409)
        if data.status == "success" and data.amount > invoice.amount_due - invoice.amount_paid:
            raise DomainError("Payment exceeds remaining unpaid amount")
        attempt = PaymentAttempt(invoice_id=invoice.id, amount=data.amount, currency=data.currency.upper(), status=data.status, provider_reference=data.provider_reference, failure_reason=data.failure_reason)
        self.repos.payment_attempts.create(attempt)
        if data.status == "success":
            invoice.amount_paid += data.amount
            invoice.status = "paid" if invoice.amount_paid == invoice.amount_due else "partially_paid"
            event_type, description = "payment_success", "Successful payment recorded"
        else:
            event_type, description = "payment_failure", data.failure_reason or "Payment failed"
        self.repos.ledger.create(LedgerEntry(customer_id=invoice.customer_id, invoice=invoice, entry_type=event_type, amount=data.amount, currency=invoice.currency, reference_id=data.provider_reference, description=description))
        try:
            self.db.commit(); self.db.refresh(attempt); self.db.refresh(invoice)
        except IntegrityError:
            self.db.rollback(); raise DomainError("Provider reference already exists", 409)
        return attempt, invoice
