# app/test_db.py
import asyncio
from database import engine

async def test_connection():
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: print("Database Connected!"))

asyncio.run(test_connection())
