import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from database.session import MongoDB
from main import app


@pytest.fixture
async def mongo_client():
    mongo_uri = "mongodb://localhost:27018"
    db_name = 'test_db'
    client = AsyncIOMotorClient(mongo_uri)
    MongoDB.client = client
    MongoDB.db_name = db_name

    yield client

    await client.drop_database(db_name)
    client.close()


@pytest.fixture
async def async_test_client(mongo_client):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
