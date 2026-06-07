from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
from .routers import game, dashboard

app = FastAPI(
    title="Chess RL API",
    description="Chess game with self-learning AI using Reinforcement Learning",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game.router)
app.include_router(dashboard.router)

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ Database tables created!")

@app.get("/")
async def root():
    return {"message": "Chess RL API is running!", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}