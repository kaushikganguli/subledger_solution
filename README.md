# SubLedger — Billing Backend

A working, modular billing backend implementing the supplied six-page SubLedger assignment. The implementation deliberately focuses on the requested foundation—not payment gateway integration, frontend, proration, taxation, authentication/RBAC, or complex subscription schedules.

## Technology

- Python 3.11+ (Docker image uses 3.12)
- FastAPI + Pydantic v2
- SQLAlchemy 2 ORM
- PostgreSQL for Docker; SQLite by default for a quick local run
- Pytest + FastAPI TestClient

## Architecture

`api/routes` contains HTTP adapters only. `services` owns business workflows and rules. `repositories` owns persistence queries and writes. `models` contains SQLAlchemy entities and relationships. `schemas` validates requests and shapes responses. `core` contains configuration and domain errors. `db.py` owns engine/session lifecycle.

See [DESIGN.md](DESIGN.md) for the ERD, responsibility matrices, rule ownership, design pattern, and invoice/payment sequence flows.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The default database is `sqlite:///./subledger.db`; tables are created on application startup. Open Swagger UI at `http://localhost:8000/docs`, ReDoc at `/redoc`, and health at `/health`.

## Run with Docker Compose (PostgreSQL)

```bash
docker compose up --build
```

API: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`. Compose uses a named PostgreSQL volume. Change the example credentials before using outside local development.

## API catalogue

All business endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/plans` | Create a plan |
| GET | `/plans` | List plans |
| PATCH | `/plans/{plan_id}` | Update plan fields or activate/deactivate |
| POST | `/customers` | Create customer |
| GET | `/customers` | List customers |
| GET | `/customers/{customer_id}` | Customer details |
| POST | `/subscriptions` | Create subscription |
| GET | `/subscriptions` | List subscriptions |
| PATCH | `/subscriptions/{subscription_id}/cancel` | Cancel subscription |
| POST | `/invoices/generate` | Generate invoice for active subscription |
| GET | `/invoices/{invoice_id}` | Invoice details |
| POST | `/payments/record` | Record successful/failed payment attempt |
| GET | `/customers/{customer_id}/ledger` | Customer ledger history |

## Example workflow

1. `POST /api/v1/plans` with `{"name":"Starter","billing_cycle":"monthly","price":"499.00","currency":"INR"}`.
2. `POST /api/v1/customers` with `{"name":"Ada","email":"ada@example.com"}`.
3. `POST /api/v1/subscriptions` with returned `customer_id` and `plan_id`.
4. `POST /api/v1/invoices/generate` with `{"subscription_id":1}`.
5. `POST /api/v1/payments/record` with `{"invoice_id":1,"amount":"200.00","currency":"INR","status":"success","provider_reference":"demo-pay-001"}`.
6. Read the invoice and `/customers/{customer_id}/ledger` to inspect state and audit events.

Money fields are decimal strings in JSON. A payment `status` is `success` or `failed`. `provider_reference` is unique to prevent duplicate attempt references.

## Tests

```bash
pytest -q
```

Tests cover positive plan price, unique customer email, inactive plan rejection, duplicate active subscription prevention, invoice price snapshot, payment overpayment prevention, partial/full payment transitions, failed payment behavior, and ledger event creation.

## Assumptions and limitations

- One active subscription per customer/plan pair; a customer may subscribe to different plans.
- Billing-cycle periods are approximated as 30/90/365 days for this learning project. Production billing should use calendar-aware month/quarter/year arithmetic and explicit timezone policy.
- Invoice amount/currency are snapshotted from the plan at invoice generation. Changing a plan later does not alter existing invoices.
- Invoice generation uses the subscription's current period unless explicit period boundaries are supplied. This version does not automatically advance the subscription period or prevent duplicate invoices for the same period.
- No external payment processor is called. Payment outcome is supplied by the caller as a simulation of a provider callback.
- The ledger has no update/delete API and an ORM session hook rejects modifications/deletions. A production deployment should additionally enforce append-only access through database roles/triggers and immutable audit storage.
- No authentication, authorization, tax, proration, refunds, dunning, webhook signature verification, or multi-tenant isolation is implemented because these are outside the brief's required scope.
- Database schema changes are created automatically for convenience; production should use Alembic migrations.
