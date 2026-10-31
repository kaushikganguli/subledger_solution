from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.errors import DomainError
from app.db import Base, engine
from app import models  # register ORM metadata
from app.api.routes import plans, customers, subscriptions, invoices, payments

@asynccontextmanager
async def lifespan(application: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", description="Modular SaaS billing backend with append-only ledger.", lifespan=lifespan)

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.get("/health", tags=["Operations"])
def health(): return {"status": "ok", "service": "subledger"}

for router in (plans.router, customers.router, subscriptions.router, invoices.router, payments.router):
    app.include_router(router, prefix=settings.api_v1_prefix)
