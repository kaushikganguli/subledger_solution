from app.repositories.repos import PlanRepository, CustomerRepository, SubscriptionRepository, InvoiceRepository, PaymentAttemptRepository, LedgerRepository
from app.services.services import PlanService, CustomerService, SubscriptionService, InvoiceService, PaymentService, LedgerService

def service_bundle(db):
    repos = type("Repositories", (), {})()
    repos.plans = PlanRepository(db); repos.customers = CustomerRepository(db)
    repos.subscriptions = SubscriptionRepository(db); repos.invoices = InvoiceRepository(db)
    repos.payment_attempts = PaymentAttemptRepository(db); repos.ledger = LedgerRepository(db)
    return {
        "plans": PlanService(db, repos), "customers": CustomerService(db, repos),
        "subscriptions": SubscriptionService(db, repos), "invoices": InvoiceService(db, repos),
        "payments": PaymentService(db, repos), "ledger": LedgerService(db, repos)
    }
