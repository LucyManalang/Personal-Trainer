"""
FastAPI application entry point.

Configures CORS, registers routers, and creates database tables on startup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, data, coach, schedule
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal AI Trainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(coach.router, prefix="/coach", tags=["Coach"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"message": "Personal AI Trainer API is running"}
