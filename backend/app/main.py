from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import orders, inventory, dashboard
from app.services.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Eluno AI - Order Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your deployed frontend URL before final submission
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "ok", "service": "eluno-oms-backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}
