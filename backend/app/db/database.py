from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Why async? Our API handles multiple requests at once
# (WebSocket dashboard + game moves + training)
# Async means it doesn't freeze while waiting for DB
DATABASE_URL = "postgresql+asyncpg://chessuser:chesspass@127.0.0.1:5433/chessrl"
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  #Logs all SQL queries - good for debugging
    connect_args={
        "ssl":False, # Disable SSL for local development. In production, use SSL for security.
    }



)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# This function gives us a DB session for each request
# Used as a dependency in FastAPI routes

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() #Save changes after each request
        except Exception :
            await session.rollback() #Undo changes if error
            raise

#Create all tables if they dont exist

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)