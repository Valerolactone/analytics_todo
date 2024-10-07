import asyncio

import uvicorn
from fastapi import APIRouter, FastAPI

from app.routers import statistics_router
from database.session import MongoDB
from kafka_consumer import KafkaConsumerManager
from settings import settings

app = FastAPI()
kafka_manager = KafkaConsumerManager(
    topic="projects_and_related_tasks_topic", group_id="core"
)


@app.on_event("startup")
async def startup_event():
    await MongoDB.connect(settings.mongo_uri, settings.mongo_db_name)
    asyncio.create_task(kafka_manager.start())


@app.on_event("shutdown")
async def shutdown_event():
    if kafka_manager.consumer:
        await kafka_manager.consumer.stop()
    await MongoDB.close()


@app.get("/")
def get_home():
    return {"data": "Hello world!"}


main_api_router = APIRouter()

main_api_router.include_router(
    statistics_router, prefix="/statistics", tags=["statistics"]
)

app.include_router(main_api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
