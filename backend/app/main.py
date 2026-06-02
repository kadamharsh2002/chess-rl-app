from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db

app=FastAPI(
    title = "Chess RL API",
    description = "Chess Game with self-learning AI using Reinforcement Learning",
    version="1.0.0"
)

## CORS  - allows our react front end to talk to this backend
#Without this, the browser blocks all the request from localhost:5173

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#When the API starts up -create all DB tables Autimatically
@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ Database tables created!")

@app.get("/")
async def root():
    return {"message": "Chess RL API is Running!","status":"ok"}
@app.get("/health")
async def health_check():
    return {"status":"healthy"}

