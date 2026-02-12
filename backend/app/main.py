from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, data, coach
from .database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal AI Running Coach")

# Allow CORS (useful for future frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(coach.router, prefix="/coach", tags=["Coach"])

@app.get("/")
def read_root():
    return {"message": "Welcome to your Personal AI Running Coach API"}
