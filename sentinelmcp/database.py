from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Integer, DateTime, Text
from datetime import datetime
import os

DB_PATH = os.getenv("LOG_DB_PATH", "audit.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(Integer, primary_key=True, index=True)
    timestamp     = Column(DateTime, default=datetime.utcnow)
    endpoint      = Column(String)
    state_hash    = Column(String)
    secrets_found = Column(Integer, default=0)
    blocked       = Column(String, default="false")
    body_preview  = Column(Text)

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("PRAGMA journal_mode=WAL")
        )
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session