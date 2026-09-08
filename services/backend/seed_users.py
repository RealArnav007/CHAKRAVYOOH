"""
Pukar — Demo User Seed Script
Run from: services/backend/
"""
import asyncio, uuid, sys, os
from datetime import datetime, timezone

import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.config import get_settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

settings = get_settings()
DB_URL = settings.DATABASE_URL

DEMO_USERS = [
    {"user_id": str(uuid.uuid4()), "email": "improve-electable82@bravealias.com", "password": "Welcome@2029",    "role": "SUPER_ADMIN"},
    {"user_id": str(uuid.uuid4()), "email": "commander@pukar.ndrf.gov.in",        "password": "Commander@2029",  "role": "COMMANDER"},
    {"user_id": str(uuid.uuid4()), "email": "responder@pukar.ndrf.gov.in",        "password": "Responder@2029",  "role": "RESPONDER"},
    {"user_id": str(uuid.uuid4()), "email": "analyst@pukar.ndrf.gov.in",          "password": "Analyst@2029",    "role": "ANALYST"},
]

def _hash(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

async def seed():
    engine = create_async_engine(DB_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as db:
        print("Wiping users/sessions/audit_events...")
        await db.execute(text("DELETE FROM sessions"))
        await db.execute(text("DELETE FROM audit_events"))
        await db.execute(text("DELETE FROM users"))
        await db.commit()
        now = datetime.now(timezone.utc)
        for u in DEMO_USERS:
            await db.execute(text(
                "INSERT INTO users (user_id,email,hashed_password,role,is_active,created_at) "
                "VALUES (:uid,:email,:hp,:role,TRUE,:now)"
            ), {"uid":u["user_id"],"email":u["email"],"hp":_hash(u["password"]),"role":u["role"],"now":now})
        await db.commit()
    await engine.dispose()
    print("")
    print("="*68)
    print(f"  {'ROLE':<14} {'EMAIL':<38} PASSWORD")
    print("="*68)
    for u in DEMO_USERS:
        print(f"  {u['role']:<14} {u['email']:<38} {u['password']}")
    print("="*68)
    print("\nUser IDs:")
    for u in DEMO_USERS:
        print(f"  [{u['role']:<12}] {u['user_id']}  {u['email']}")
    print("\nDone.")

asyncio.run(seed())
