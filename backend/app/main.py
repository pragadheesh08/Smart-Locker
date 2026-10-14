

# app.py

from contextlib import asynccontextmanager

from app.db import Base, engine
from app.lockers.router import router as lockers_router
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables at startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart Locker API",
    description="Backend API for the Smart Locker Demonstration",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(lockers_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Smart Locker API is running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
