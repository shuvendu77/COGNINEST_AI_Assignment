from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.agent import agent_memory
from app.memory.seeder import seed_memory_instance
from app.controllers.chat import router as chat_router
from app.controllers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    seeded = await seed_memory_instance(agent_memory)
    print(f"Agent memory seeded with {seeded} Q&A pairs.")
    yield


app = FastAPI(title="Clinic NLP-to-SQL API", lifespan=lifespan)

app.include_router(chat_router)
app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)

