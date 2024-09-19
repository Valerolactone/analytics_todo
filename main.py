import uvicorn
from fastapi import APIRouter, FastAPI

from app.routers import statistics_router
from database.session import MongoDB
from settings import settings

app = FastAPI()


@app.on_event("startup")
async def startup_db_client():
    await MongoDB.connect(settings.mongo_uri, settings.mongo_db_name)


@app.on_event("shutdown")
async def shutdown_db_client():
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
