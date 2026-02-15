from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, data, coach, schedule
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal AI Running Coach")

# Allow CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    return {"message": "Welcome to your Personal AI Running Coach API"}
