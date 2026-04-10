import sqlite3

from fastapi import APIRouter

from app.core.agent import agent_memory
from app.core.config import get_db_path

router = APIRouter()


@router.get("/health")
async def health():
    try:
        conn = sqlite3.connect(get_db_path())
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    try:
        memory_items = len(getattr(agent_memory, "_memories", []))
    except Exception:
        memory_items = 0

    return {
        "status": "ok",
        "database": db_status,
        "agent_memory_items": memory_items,
    }
