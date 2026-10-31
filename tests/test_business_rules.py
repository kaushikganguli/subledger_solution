from decimal import Decimal

def create_plan(client, price="100.00", status="active"):
    r = client.post("/api/v1/plans", json={"name":"Starter", "billing_cycle":"monthly", "price":price, "currency":"INR"})
    assert r.status_code == 201, r.text
    if status == "inactive":
        r = client.patch(f"/api/v1/plans/{r.json()['id']}", json={"status":"inactive"})
        assert r.status_code == 200
    return r.json()

def create_customer(client, email="one@example.com"):
    r = client.post("/api/v1/customers", json={"name":"A Customer", "email":email})
    assert r.status_code == 201, r.text
    return r.json()

def create_subscription(client, customer_id, plan_id):
    return client.post("/api/v1/subscriptions", json={"customer_id":customer_id,"plan_id":plan_id})

def create_invoice(client):
    plan = create_plan(client)
    customer = create_customer(client)
    sub = create_subscription(client, customer["id"], plan["id"])
    assert sub.status_code == 201, sub.text
    invoice = client.post("/api/v1/invoices/generate", json={"subscription_id":sub.json()["id"]})
    assert invoice.status_code == 201, invoice.text
    return invoice.json(), customer

def test_plan_price_must_be_positive(client):
    r = client.post("/api/v1/plans", json={"name":"Free", "price":0, "billing_cycle":"monthly", "currency":"INR"})
    assert r.status_code == 422

def test_customer_email_must_be_unique(client):
    create_customer(client)
    r = client.post("/api/v1/customers", json={"name":"Duplicate", "email":"one@example.com"})
    assert r.status_code == 409

def test_inactive_plan_cannot_be_subscribed(client):
    plan = create_plan(client, status="inactive")
    customer = create_customer(client)
    r = create_subscription(client, customer["id"], plan["id"])
    assert r.status_code == 400

def test_duplicate_active_subscription_is_rejected(client):
    plan = create_plan(client); customer = create_customer(client)
    assert create_subscription(client, customer["id"], plan["id"]).status_code == 201
    assert create_subscription(client, customer["id"], plan["id"]).status_code == 409

def test_invoice_uses_plan_price_snapshot(client):
    invoice, _ = create_invoice(client)
    assert Decimal(invoice["amount_due"]) == Decimal("100.00")

def test_successful_payment_cannot_exceed_balance(client):
    invoice, _ = create_invoice(client)
    r = client.post("/api/v1/payments/record", json={"invoice_id":invoice["id"],"amount":"100.01","currency":"INR","status":"success","provider_reference":"pay-over"})
    assert r.status_code == 400

def test_partial_then_full_payment_updates_invoice(client):
    invoice, _ = create_invoice(client)
    r1 = client.post("/api/v1/payments/record", json={"invoice_id":invoice["id"],"amount":"40.00","currency":"INR","status":"success","provider_reference":"pay-part"})
    assert r1.status_code == 201 and r1.json()["invoice"]["status"] == "partially_paid"
    r2 = client.post("/api/v1/payments/record", json={"invoice_id":invoice["id"],"amount":"60.00","currency":"INR","status":"success","provider_reference":"pay-rest"})
    assert r2.status_code == 201 and r2.json()["invoice"]["status"] == "paid"

def test_failed_payment_does_not_increase_amount_paid(client):
    invoice, _ = create_invoice(client)
    r = client.post("/api/v1/payments/record", json={"invoice_id":invoice["id"],"amount":"100.00","currency":"INR","status":"failed","provider_reference":"pay-fail","failure_reason":"Declined"})
    assert r.status_code == 201
    assert Decimal(r.json()["invoice"]["amount_paid"]) == Decimal("0.00")
    assert r.json()["invoice"]["status"] == "issued"

def test_ledger_contains_invoice_and_payment_events(client):
    invoice, customer = create_invoice(client)
    client.post("/api/v1/payments/record", json={"invoice_id":invoice["id"],"amount":"10.00","currency":"INR","status":"failed","provider_reference":"ledger-ref"})
    r = client.get(f"/api/v1/customers/{customer['id']}/ledger")
    assert r.status_code == 200
    assert {x["entry_type"] for x in r.json()} == {"invoice_created", "payment_failure"}
