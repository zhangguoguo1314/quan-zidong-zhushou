from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import engine, Base
from api.routes import auth, sites, accounts, tasks, logs
from tasks.scheduler import start_scheduler, stop_scheduler, scheduler

app = FastAPI(title="Account-Auto-Sign API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sites.router)
app.include_router(accounts.router)
app.include_router(tasks.router)
app.include_router(logs.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    if not scheduler.running:
        start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        stop_scheduler()


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
