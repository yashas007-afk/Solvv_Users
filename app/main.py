from fastapi import FastAPI
from app.routes import users
from app.database.user import engine, Base

app = FastAPI(title="Solvv Admin API")

# Create tables on startup
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include routers
app.include_router(users.router)
